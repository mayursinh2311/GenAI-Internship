
import os
import json

from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))


# --------------------------------
# COLLEGE DATABASE (DEMO)
# --------------------------------

students = {
    "ST101": "Name: Rahul, Course: BCA, Semester: 5",
    "ST102": "Name: Amit, Course: BCA, Semester: 3",
    "ST103": "Name: Priya, Course: BBA, Semester: 4"
}

fees = {
    "ST101": "Total Fees: Rs 25000, Paid: Rs 20000, Pending: Rs 5000",
    "ST102": "Total Fees: Rs 22000, Paid: Rs 22000, Pending: Rs 0",
    "ST103": "Total Fees: Rs 30000, Paid: Rs 25000, Pending: Rs 5000"
}

attendance = {
    "ST101": "Present: 85%, Absent: 15%",
    "ST102": "Present: 90%, Absent: 10%",
    "ST103": "Present: 75%, Absent: 25%"
}


# --------------------------------
# TOOLS
# --------------------------------

def check_student(student_id):

    student_id = student_id.upper()

    if student_id in students:
        return students[student_id]

    return "Student not found."


def check_fees(student_id):

    student_id = student_id.upper()

    if student_id in fees:
        return fees[student_id]

    return "Fee record not found."


def check_attendance(student_id):

    student_id = student_id.upper()

    if student_id in attendance:
        return attendance[student_id]

    return "Attendance record not found."


# --------------------------------
# TOOL EXECUTOR
# --------------------------------

def run_tool(name, args):

    if name == "check_student":
        return check_student(args["student_id"])

    elif name == "check_fees":
        return check_fees(args["student_id"])

    elif name == "check_attendance":
        return check_attendance(args["student_id"])

    else:
        return "Unknown tool"


# --------------------------------
# STUDENT TOOLS
# --------------------------------

student_tools = [
    {
        "type": "function",
        "function": {
            "name": "check_student",
            "description": "Get student details using student ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string",
                        "description": "Example ST101"
                    }
                },
                "required": ["student_id"]
            }
        }
    }
]


# --------------------------------
# FEES TOOLS
# --------------------------------

fees_tools = [
    {
        "type": "function",
        "function": {
            "name": "check_fees",
            "description": "Check student college fee details",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string"
                    }
                },
                "required": ["student_id"]
            }
        }
    }
]


# --------------------------------
# ATTENDANCE TOOLS
# --------------------------------

attendance_tools = [
    {
        "type": "function",
        "function": {
            "name": "check_attendance",
            "description": "Check student attendance percentage",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {
                        "type": "string"
                    }
                },
                "required": ["student_id"]
            }
        }
    }
]


# --------------------------------
# SPECIALIST AGENT
# --------------------------------

def run_specialist(system_prompt, query, tools):

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": query
        }
    ]

    response = client.chat.complete(
        model="mistral-small-latest",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    msg = response.choices[0].message

    if msg.tool_calls:

        messages.append(msg)

        for tc in msg.tool_calls:

            args = json.loads(tc.function.arguments)

            result = run_tool(
                tc.function.name,
                args
            )

            print(f"{tc.function.name} => {result}")

            messages.append({
                "role": "tool",
                "name": tc.function.name,
                "content": str(result),
                "tool_call_id": tc.id
            })

        final = client.chat.complete(
            model="mistral-small-latest",
            messages=messages
        )

        return final.choices[0].message.content

    return msg.content


# --------------------------------
# ROUTER AGENT
# --------------------------------

def route(query):

    r = client.chat.complete(
        model="mistral-small-latest",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": """
                You are a college query router.

                Reply with ONE word only:

                student - Student details and information.
                fees - College fees and payment details.
                attendance - Attendance and presence details.
                general - Everything else.
                """
            },
            {
                "role": "user",
                "content": query
            }
        ]
    )

    return r.choices[0].message.content.strip().lower()


# --------------------------------
# MAIN APPLICATION
# --------------------------------

query = input("Student: ")

category = route(query)

print(f"Routed to: {category} Agent")


if category == "student":

    answer = run_specialist(
        "You are a helpful college student information agent. Use the check_student tool to answer student detail questions. Do not invent student records.",
        query,
        student_tools
    )

elif category == "fees":

    answer = run_specialist(
        "You are a college fees support agent. Use the check_fees tool to provide fee information. Do not invent payment records.",
        query,
        fees_tools
    )

elif category == "attendance":

    answer = run_specialist(
        "You are a college attendance support agent. Use the check_attendance tool to provide attendance information. Do not invent attendance records.",
        query,
        attendance_tools
    )

else:

    answer = run_specialist(
        "You are a helpful college support agent. Answer general college questions politely. Do not make up official college policies.",
        query,
        []
    )


print("\nCollege Support:", answer)
