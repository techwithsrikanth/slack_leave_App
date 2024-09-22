
import requests
import json
from datetime import datetime
from django.shortcuts import render
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from dotenv import load_dotenv
import os
from django.conf import settings

token = settings.SLACK_TOKEN
print('token', token)


user_mapping = {
    "U07KCUN24TZ": "jamesbilly",
    "U07KTFLHJ66": "srikanthanprakash2003",
    "U07KW0E0ESY": "srikanthprakash072003"
}
manager_mapping = {
    "srikanthanprakash2003": "srikanthprakash072003",
    "jamesbilly": "srikanthprakash072003",
}
leave_requests = {}
leave_statistics = {}

def send_apply_leave_button(user_id):
    url = 'https://slack.com/api/views.publish'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    data = {
        "user_id": user_id,
        "view": {
            "type": "home",
            "blocks": [
                {
                    "type": "section",
                    "block_id": "welcome_block",
                    "text": {
                        "type": "mrkdwn",
                        "text": ":wave: *Welcome to the Leave Management App!* :blush:\n\nWe are here to make managing your leave simple and easy! Whether you need some time off or want to check your leave balance, you're in the right place. :rocket:\n\nTake a break, refresh yourself, and we’ll handle the rest! :palm_tree:"
                    }
                },
                {
                    "type": "actions",
                    "block_id": "actions_block",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "🌟 Apply Leave"
                            },
                            "action_id": "apply_leave"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "📊 Leave Statistics"
                            },
                            "action_id": "leave_statistics"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "👥 Team Member Leave"
                            },
                            "action_id": "team_member_leave",
                            "url": "https://ec5b-14-99-67-22.ngrok-free.app/slack/calender"
                        }
                    ]
                }
            ]
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status() 
    print(response.json())

 

def send_leave_statistics(user_id, trigger_id):
    url = 'https://slack.com/api/views.open'
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json; charset=utf-8'}
    
    user_name = user_mapping.get(user_id, None)
    if not user_name:
        return
    manager = manager_mapping.get(user_name, None)
    
    managed_employees = [emp_id for emp_id, emp_name in user_mapping.items() if manager_mapping.get(emp_name) == user_name]
    print('managed employees', managed_employees)
    managed_employees.append(user_id)
    
    blocks = [
        {
            "type": "input",
            "block_id": "user_block",
            "label": {
                "type": "plain_text",
                "text": "Select User"
            },
            "element": {
                "type": "static_select",
                "action_id": "user_select",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select a user"
                },
                "options": [
                    {
                        "text": {
                            "type": "plain_text",
                            "text": user_mapping.get(emp_id, 'Unknown')
                        },
                        "value": emp_id
                    } for emp_id in managed_employees
                ]
            }
        },
        {
            "type": "actions",
            "block_id": "filter_block",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Filter"
                    },
                    "action_id": "filter_button"
                }
            ]
        },
        {
            "type": "section",
            "block_id": "leave_statistics_block",
            "text": {
                "type": "mrkdwn",
                "text": "*Leave Statistics*"
            }
        },
        {
            "type": "divider"
        }
    ]
    
    for emp_id in managed_employees:
        if emp_id in leave_statistics:
            stats = leave_statistics[emp_id]
            leave_taken = stats.get('leave_taken', 0)
            last_details = stats.get('details', [])[-1] if stats.get('details') else {}
            constraints = last_details.get('leave_constraints', {})

            constraints_text = '\n'.join([f"*{leave_type}*: {days} days" for leave_type, days in constraints.items()])

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Leave Statistics for {user_mapping.get(emp_id, 'Unknown')}*\n"
                            f"Leave Taken: *{leave_taken}* days\n\n"
                            f"*Leave Constraints:*\n{constraints_text}"
                }
            })
        else:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Leave Statistics for {user_mapping.get(emp_id, 'Unknown')}*\n"
                            f"No leave statistics found."
                }
            })
        blocks.append({"type": "divider"})
    
    data = {
        "trigger_id": trigger_id,
        "view": {
            "type": "modal",
            "callback_id": "leave_statistics_modal",
            "title": {
                "type": "plain_text",
                "text": "Leave Statistics"
            },
            "blocks": blocks,
            "submit": {
                "type": "plain_text",
                "text": "Submit"
            }
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    print(response.json())



def filter_leave_statistics(user_id):
    filtered_data = {}
    
    if user_id in leave_statistics:
        filtered_data[user_id] = leave_statistics[user_id]
    
    return filtered_data

def update_modal(view_id, filtered_data):
    url = 'https://slack.com/api/views.update'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json; charset=utf-8'
    }
    print('filtered data in update modal', filtered_data)
    
    blocks = [
        {
            "type": "section",
            "block_id": "leave_statistics_block",
            "text": {
                "type": "mrkdwn",
                "text": "*Leave Statistics*"
            }
        },
        {
            "type": "divider"
        }
    ]

    for emp_id, stats in filtered_data.items():
        leave_taken = stats['leave_taken']
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Leave Statistics for {user_mapping.get(emp_id, 'Unknown')}*\nTotal Leave Days Taken: {leave_taken}"
            }
        })
        blocks.append({"type": "divider"})
        
        for leave in stats['details']:
            start_date = leave.get('start_date', 'N/A')
            end_date = leave.get('end_date', 'N/A')
            reason = leave.get('reason', 'N/A')
            
            blocks.append({
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Start Date:*\n{start_date}"},
                    {"type": "mrkdwn", "text": f"*End Date:*\n{end_date}"},
                    {"type": "mrkdwn", "text": f"*Reason:*\n{reason}"}
                ]
            })
            blocks.append({"type": "divider"})

        constraints = leave.get('leave_constraints', {})
        if constraints:
            constraints_text = '\n'.join([f"*{leave_type}*: {days} days" for leave_type, days in constraints.items()])
            blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Leave constraints left:*\n{constraints_text}"
                    }
                })
            
        blocks.append({"type": "divider"})

    data = {
        "view_id": view_id,
        "view": {
            "type": "modal",
            "callback_id": "leave_statistics_modal",
            "title": {
                "type": "plain_text",
                "text": "Leave Statistics"
            },
            "blocks": blocks
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()  
    print(response.json())




def send_leave_request_form(user_id, trigger_id):
    url = 'https://slack.com/api/views.open'
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    data = {
        "trigger_id": trigger_id,
        "view": {
            "type": "modal",
            "callback_id": "leave_request_modal",
            "title": {
                "type": "plain_text",
                "text": "Leave Request"
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "leave_type_block",
                    "label": {
                        "type": "plain_text",
                        "text": "Leave Type"
                    },
                    "element": {
                        "type": "static_select",
                        "action_id": "leave_type",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select leave type"
                        },
                        "options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Casual Leave (CL)"
                                },
                                "value": "casual_leave"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Sick Leave (SL)"
                                },
                                "value": "sick_leave"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Maternity Leave (ML)"
                                },
                                "value": "maternity_leave"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Marriage Leave"
                                },
                                "value": "marriage_leave"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Paternity Leave"
                                },
                                "value": "paternity_leave"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Bereavement Leave"
                                },
                                "value": "bereavement_leave"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Compensatory Off (comp-off)"
                                },
                                "value": "comp_off"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Loss Of Pay Leave (LOP/LWP)"
                                },
                                "value": "loss_of_pay"
                            }
                        ]
                    }
                },
                {
                    "type": "input",
                    "block_id": "start_date_block",
                    "label": {
                        "type": "plain_text",
                        "text": "Start Date"
                    },
                    "element": {
                        "type": "datepicker",
                        "action_id": "start_date"
                    },
                    "optional": False
                },
                {
                    "type": "input",
                    "block_id": "end_date_block",
                    "label": {
                        "type": "plain_text",
                        "text": "End Date"
                    },
                    "element": {
                        "type": "datepicker",
                        "action_id": "end_date"
                    },
                    "optional": False
                },
                {
                    "type": "input",
                    "block_id": "reason_block",
                    "label": {
                        "type": "plain_text",
                        "text": "Reason for leave"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "leave_reason",
                        "multiline": True
                    },
                    "optional": False
                },
                {
                    "type": "actions",
                    "block_id": "submit_block",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Submit"
                            },
                            "action_id": "submit_leave_request"
                        }
                    ]
                }
            ],
            "private_metadata": trigger_id, 
            "submit": {
                "type": "plain_text",
                "text": "Submit"
            }
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    print("Status Code:", response.status_code)
    print("Response Text:", response.text)



def send_leave_request_to_manager(manager_username, user_id, start_date, end_date,leave_type, reason):
    url = 'https://slack.com/api/chat.postMessage'
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    manager_id = None
    for user_id_key, username in user_mapping.items():
        if username == manager_username:
            manager_id = user_id_key
            break
    if manager_id is None:
        print(f"No Slack user ID found for manager username: {manager_username}")
        return

    manager_message = f"Leave Request from {user_mapping.get(user_id)}:\nStart Date: {start_date}\nEnd Date: {end_date}\nLeave Type: {leave_type}\nReason: {reason}\nStatus: Pending"
    data = {
        "channel": manager_id,
        "text": manager_message,
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": manager_message}
            },
            {
                "type": "actions",
                "block_id": "manager_actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Approve"},
                        "action_id": "approve_request",
                        "value": json.dumps({"user_id": user_id, "status": "Approved"}),
                        "style": "primary"  # Green button
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Reject"},
                        "action_id": "reject_request",
                        "value": json.dumps({"user_id": user_id, "status": "Rejected"}),
                        "style": "danger"  
                    }
                ]
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    response_data = response.json()
    print('response data of manager', response_data)
    return response_data.get('ts'), response_data.get('channel')

def send_message_to_user(user_id, message):
    url = 'https://slack.com/api/chat.postMessage'
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    data = {
        "channel": user_id,
        "text": message
    }
    response = requests.post(url, headers=headers, json=data)
    response_data = response.json()
    print('response data of user ', response_data)
    return response_data.get('ts'), response_data.get('channel')


def send_message_to_manager(manager_id, message, channel_id):
    url = 'https://slack.com/api/chat.postMessage'
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    data = {
        "channel": channel_id,
        "text": message
    }
    response = requests.post(url, headers=headers, json=data)
    response_data = response.json()
    print('response data of manager ', response_data)
    return response_data.get('ts')
def update_message(channel_id, ts, message):
    url = 'https://slack.com/api/chat.update'
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    data = {
        "channel": channel_id,
        "ts": ts,
        "text": message
    }
    requests.post(url, headers=headers, json=data)

def send_leave_summary(user_id, manager_id, start_date, end_date, reason, leave_type, leave_requests, leave_constraints):
    """Send leave summary to both the user and the manager."""
    user_message = f"Leave Request Summary:\nStart Date: {start_date}\nEnd Date: {end_date}\nReason: {reason}\nLeave Type: {leave_type}\nStatus: Pending"
    manager_message = f"Leave Request from {user_mapping.get(user_id)}:\nStart Date: {start_date}\nEnd Date: {end_date}\nReason: {reason}\nLeave Type: {leave_type}\nStatus: Pending"

    user_ts, user_channel_id = send_message_to_user(user_id, user_message)
    print('user_ts', user_ts)
    print('user_channel', user_channel_id)
    manager_channel_id = None
    manager_ts = None
    if manager_id:
        manager_ts, manager_channel_id = send_leave_request_to_manager(manager_id, user_id, start_date, end_date, leave_type, reason)
        print('manager_ts', manager_ts)
        print('manager_channel', manager_channel_id)
    leave_requests[user_id] = {'user_id': user_id, 'user_ts': user_ts, 'manager_ts': manager_ts, 'start_date': start_date, 'end_date': end_date, 'reason': reason, 'leave_constraints' : leave_constraints}
    print('leave_requests in 514', leave_requests)
    print('leave_constraints in 515', leave_constraints)
    if manager_id is None:
        handle_manager_response(user_id, 'Approved', manager_channel_id, manager_id, user_channel_id, leave_requests, leave_constraints)
    else:
        return user_channel_id, manager_channel_id
def handle_manager_response(user_id, status, channel_id2, manager_id, channel_id, leave_requests1, leave_constraints):
    print('leave requests here', leave_requests1)
    
    if user_id not in leave_requests1:
        print(f"User ID {user_id} not found in leave_requests.")
        return

    leave_request = leave_requests1[user_id]
    start_date = leave_request.get('start_date', 'N/A')  
    end_date = leave_request.get('end_date', 'N/A')  
    reason = leave_request.get('reason', 'No reason provided')  
    from_user = user_mapping.get(user_id, 'Unknown user')

    if manager_id is None:
        status = 'Approved'
        print(f"No manager found for user ID {user_id}. Automatically approving leave request.")

    status_update = (
        f"Leave Request Status Update for {from_user}:\n"
        f"Start Date: {start_date}\n"
        f"End Date: {end_date}\n"
        f"Reason: {reason}\n"
        f"Status: {status}"
    )

    status_update2 = (
        f"Recent Leave Request Status Update for you:\n"
        f"Start Date: {start_date}\n"
        f"End Date: {end_date}\n"
        f"Reason: {reason}\n"
        f"Status: {status}"
    )

    user_ts = leave_request.get('user_ts')
    manager_ts = leave_request.get('manager_ts')
    
    print('channel_id in line 594', channel_id)
    print('channel_id2 in line 595', channel_id2 )
    print('status update2 in 299', status_update2)
    print('user ts in 300', user_ts)

    if user_ts:
        update_message(channel_id, user_ts, status_update2)

    if manager_ts:
        update_message(channel_id2, manager_ts, status_update)

    leave_days = (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days + 1

    if user_id not in leave_statistics:
        leave_statistics[user_id] = {
            'leave_taken': 0,
            'details': []
        }
    

    if status == 'Approved':
        leave_statistics[user_id]['leave_taken'] += leave_days
        print('leave_requests in 593 approved ', leave_requests1 )

        leave_statistics[user_id]['details'].append({
            'start_date': start_date,
            'end_date': end_date,
            'reason': reason,
            'leave_constraints': leave_constraints
        })

        print('leave_statistics in 582', leave_statistics)


def render_calendar(request):
    leave_data = {}
    print('leave_Requests in calendar', leave_requests)
    for user_id, details in leave_statistics.items():
        formatted_details = []

        for leave in details['details']:
            formatted_details.append({
                'start_date': leave.get('start_date', 'Unknown'),
                'end_date': leave.get('end_date', 'Unknown'),
                'reason': leave.get('reason', 'No reason provided')
            })
        leave_data[user_id] = formatted_details

    leave_data_json = json.dumps(leave_data)
    print("Rendering calendar with leave_data:", leave_data_json)  
    return render(request, 'calender.html', {'leave_data': leave_data_json})
def close_modal(view_id):
    url = 'https://slack.com/api/views.update'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    data = {
        "view_id": view_id,
        "view": {
            "type": "modal",
            "callback_id": "leave_request_modal",
            "title": {
                "type": "plain_text",
                "text": "Leave Request"
            },
            "blocks": [], 
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"Failed to close modal: {response.text}")
