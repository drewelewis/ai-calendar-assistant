class M365Prompts:
    """
    A class to store and manage all prompts used in the AI knowledge base.
    """
    def __init__(self):
        # Example prompts, add or modify as needed
        
        self.master_prompt_str = (
            """ 
                You are a meeting scheduling assistant.
                You will help the user to schedule, update, query, and manage meetings.
                Your primary goal is to ensure that meetings are scheduled efficiently and effectively.

                Your goals are to:
                Identify the user.
                Greet the user.
                Get all organization departments.
                Identify the user's department.
                Identify the user's manager.
                Identify if the user is a manager.
                If the user has direct reports, they are a manager.
                Get the user's team.
                If the user is a manager, their team is their direct reports.
                If the user is not a manager, their team includes their manager and their manager's direct reports.
                Identify the user's team members.
                Identify the user's department members.
                Then you will help the user to schedule, update, query, and manage meetings.
                You will use the Microsoft Graph API to access user data, calendar events, and other relevant

                """.strip()
        )
        self.search_prompt = (
            "Please enter your query to search the knowledge base."
        )
        self.no_result_prompt = (
            "Sorry, I couldn't find any information related to your query."
        )
        self.feedback_prompt = (
            "Was this information helpful? Please provide your feedback."
        )

    def master_prompt(self):
        return self.master_prompt_str

    def get_search_prompt(self):
        return self.search_prompt

    def get_no_result_prompt(self):
        return self.no_result_prompt

    def get_feedback_prompt(self):
        return self.feedback_prompt

    # Add more methods or prompts as needed

prompts= M365Prompts()