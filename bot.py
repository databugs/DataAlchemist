from telegram import Update
from telegram.ext import (CommandHandler,
                          ConversationHandler, MessageHandler, filters, ContextTypes)
from logging import warning
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from pydantic import BaseModel, Field, validator
import os

class ProjectIdeas(BaseModel):
    project_ideas: list[str] = Field(description="List of project ideas.")
    
class Job(BaseModel):
    title: str

    @validator('title')
    def is_valid_job(cls, value: str):
        valid_jobs = ['data scientist', 'machine learning engineer', 'data analyst', 'data engineer', 'statistician', 'ml researcher', 'data architect', 'data mining engineer', 'applied ml scientist', 'data science manager', 'ml ops engineer', 'data science intern', 'research data scientist', 'senior data scientist', 'lead data scientist', 'principal data scientist', 'chief data scientist', 'business intelligence analyst']
        if value.lower() not in valid_jobs:
            raise ValueError('Oops! Only Data Science and Analytics jobs are allowed for now! You can /start over!')
        return value

output_parser = PydanticOutputParser(pydantic_object=ProjectIdeas)

def custom_output_parser(llm_output: str):
    if len(output_parser.parse(llm_output.replace("\n", "")).project_ideas)==5:
        return output_parser.parse(llm_output.replace("\n", "")).project_ideas
    ideas: ProjectIdeas = output_parser.parse(llm_output.replace('\n', ''))
    ideas_list = ideas.project_ideas[0]
    return [idea.strip() for idea in ideas_list.split(',')]

def setup(job=None, level=None, industry=None):
    openai_api_key = os.environ.get('OPENAI_API_KEY')

    #output_parser = PydanticOutputParser(pydantic_object=ProjectIdeas)

    format_instructions = output_parser.get_format_instructions()

    template = """
    You are The Data Alchemist, a bot for a career growth and acceleration website.
    Your job is to generate a list of recommended projects that will lead to career growth,
    given a job title, Level, and Industry of the use case.
    
    Output Format:
    1. Project 1,
    2. Project 2,
    3. Project 3,
    4. Project 4,
    5. Project 5.

    {format_instructions}

    INPUT:
    List 5 recommended projects for {job_title}, {level}, {industry}

    YOUR RESPONSE:
    """

    prompt = PromptTemplate(
        template=template,
        input_variables=["job_title", "level", "industry"],
        partial_variables={"format_instructions": format_instructions}
    )

    model = OpenAI(temperature=0.7)

    _input = prompt.format(job_title=job, level=level, industry=industry)
    return model(_input)

async def hello(update: Update, context) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}. I am The Data Alchemist. Click on /start to get started!')


async def start(update: Update, context):
    """Welcome the user and ask for their job title."""
    await update.message.reply_text("Hi, I am The Data Alchemist, your AI assistant.\nI am here to help you get started with your career growth.\nPlease tell me your job title.")
    return 1


async def job_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save the job title and ask for the job level."""
    try:
        job = Job(title=update.message.text)
        context.user_data['job_title'] = job.title
        await update.message.reply_text(f"Got it, your job title is {context.user_data['job_title']}. What is your job level?")
        return 2
    except ValueError as e:
        error_message = e.errors()[0]['msg']
        await update.message.reply_text(error_message)
        return ConversationHandler.END

async def job_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save the job level and ask for the industry."""
    context.user_data['job_level'] = update.message.text
    await update.message.reply_text(
        "Thanks. Finally, what industry are you looking to work in?")
    return 3


async def industry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save the industry and display the gathered information."""
    context.user_data['industry'] = update.message.text
    output = setup(job=context.user_data['job_title'], level=context.user_data['job_level'], industry=context.user_data['industry'])
    list_of_ideas = custom_output_parser(output)
    message = f'Here are 5 projects you can complete to take your career to the next level.\n\n{list_of_ideas[0]}\n\n{list_of_ideas[1]}\n\n{list_of_ideas[2]}\n\n{list_of_ideas[3]}\n\n{list_of_ideas[4]}\n\nGood Luck!'
    await update.message.reply_text(
        f"Here's the information I gathered: \nJob Title: {context.user_data['job_title'].title()}\nJob Level: {context.user_data['job_level'].title()}\nIndustry: {context.user_data['industry'].title()}\n\n{message}"
    )
    return ConversationHandler.END

async def cancel(update: Update, context):
    """Cancel the conversation."""
    await update.message.reply_text('Bye! I canceled the conversation.')
    return ConversationHandler.END


async def error(update: Update, context):
    """Log Errors caused by Updates."""
    warning('Update "%s" caused error "%s"', update, context.error)


conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        1: [MessageHandler(filters=filters.TEXT & (~filters.COMMAND), callback=job_title)],
        2: [MessageHandler(filters=filters.TEXT & (~filters.COMMAND), callback=job_level)],
        3: [MessageHandler(filters=filters.TEXT & (~filters.COMMAND), callback=industry)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
    , per_user=True
)

