import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from django.shortcuts import render


from .slackbot_logic import send_apply_leave_button, send_leave_request_form, send_leave_request_to_manager, send_message_to_user, update_message, handle_manager_response, send_leave_summary, send_leave_statistics, update_modal, filter_leave_statistics, render_calendar, close_modal
from jinja2 import Template
import json

# def render_calendar(request):
#     leave_data = {
#         'U07KTFLHJ66': [{'start_date': '2024-09-21', 'end_date': '2024-09-23', 'leave_days': 3, 'status': 'Pending', 'reason': 'gg'}]
#     }
    
#     leave_data_json = json.dumps(leave_data)
#     print("Rendering calendar with leave_data:", leave_data_json)  # Debugging log
#     return render(request, 'calender.html', {'leave_data': leave_data_json})


user_mapping = {
    "U07KCUN24TZ": "jamesbilly",
    "U07KTFLHJ66": "srikanthanprakash2003",
    "U07KW0E0ESY": "srikanthprakash072003"
}

manager_mapping = {
    "srikanthanprakash2003": "srikanthprakash072003",
    "jamesbilly": "srikanthprakash072003",
    # "srikanthprakash072003":"srikanthanprakash2003" 
}


leave_requests = {} 

@csrf_exempt
def slack_event_handler(request):
    """Handle Slack events like app mentions and app home opened."""
    if request.method == 'POST':
        body = json.loads(request.body.decode('utf-8'))
        
        if 'challenge' in body:
            return JsonResponse({'challenge': body['challenge']})

        event_data = body.get('event', {})
        if event_data.get('type') == 'app_home_opened':
            user_id = event_data.get('user')
            
            if event_data.get('tab') == 'home':
                send_apply_leave_button(user_id)  
        return JsonResponse({'status': 'Event received'})
    
    return HttpResponse(status=405)


user_channel_id = None
manager_channel_id = None

leave_constraints_template = {
    'Casual Leave (CL)': 12,
    'Sick Leave (SL)': 8,
    'Maternity Leave (ML)': 90,
    'Marriage Leave': 5,
    'Paternity Leave': 10,
    'Bereavement Leave': 7,
    'Compensatory Off (comp-off)': 5,
    'Loss Of Pay Leave (LOP/LWP)': 0
}

user_leave_constraints = {}


@csrf_exempt
def slack_action_handler(request):
    global user_channel_id, manager_channel_id
    if request.method == 'POST':
        payload = json.loads(request.POST.get('payload'))
        print('Payload:', payload)
        if 'actions' in payload:
            action_id = payload['actions'][0]['action_id']
            user_id = payload['user']['id']
            trigger_id = payload['trigger_id']

            if action_id == 'apply_leave':
                print('payload in line 72 ', payload)
                # channel_id = payload['container']['channel_id']
                # channel_iddum = channel_id
                send_leave_request_form(user_id, trigger_id)
            

            elif action_id == 'submit_leave_request':
                print('payload in submit_leave_request', payload)
                state = payload['view']['state']['values']
                start_date = state['start_date_block']['start_date']['selected_date']
                end_date = state['end_date_block']['end_date']['selected_date']
                reason = state['reason_block']['leave_reason']['value']
                leave_type = state['leave_type_block']['leave_type']['selected_option']['text']['text']

                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                cur_date = datetime.now().date()
                
                if start_date_obj > end_date_obj:
                    update_message(payload['response_url'], "Error: Start date cannot be after the end date.")
                    return

                if start_date_obj < cur_date or end_date_obj < cur_date:
                    update_message(payload['response_url'], "Error: Leave dates cannot be in the past.")
                    return

                leave_days = (end_date_obj - start_date_obj).days + 1
                username = user_mapping.get(user_id, None)
                manager = manager_mapping.get(username, None)

                if user_id not in user_leave_constraints:
                    user_leave_constraints[user_id] = leave_constraints_template.copy()

                user_leave_balance = user_leave_constraints[user_id]
                available_leave = user_leave_balance.get(leave_type, 0)
                print('available_leave in 118', available_leave)

                if user_id not in leave_requests:
                    leave_requests[user_id] = {
                        'leave_taken': 0, 
                        'details': []
                    }
                if 'leave_taken' not in leave_requests[user_id]:
                    leave_requests[user_id]['leave_taken'] = 0

                if 'details' not in leave_requests[user_id]:
                    leave_requests[user_id]['details'] = []

                if leave_days > available_leave:
                    lop_days = leave_days - available_leave  
                    leave_summary = f"{available_leave} days of {leave_type} and {lop_days} days of Loss of Pay."
                    
                    user_leave_balance['Loss Of Pay Leave (LOP/LWP)'] += lop_days
                    user_leave_balance[leave_type] = 0
                    leave_type = 'Loss Of Pay Leave (LOP/LWP)'
                else:
                    leave_summary = f"{leave_days} days of {leave_type}."
                    user_leave_balance[leave_type] -= leave_days
                    print('leave balance for user in 138', user_leave_balance[leave_type])

                leave_requests[user_id]['leave_taken'] += leave_days
                leave_requests[user_id]['details'].append({
                    'start_date': start_date,
                    'end_date': end_date,
                    'leave_days': leave_days,
                    'status': 'Pending',
                    'reason': reason,
                    'leave type': leave_type
                })

                print('leave requests in 257', leave_requests)

                if manager is None:
                    print(f"No manager found for {username}. Automatically approving leave.")
                    send_leave_summary(user_id, manager, start_date, end_date, reason, leave_type, leave_requests, user_leave_balance)
                    close_modal(payload['view']['id'])

                if manager:
                    print('leave_requests in 173', leave_requests)
                    print('user_leave_balance in 174', user_leave_balance)
                    user_channel_id, manager_channel_id = send_leave_summary(user_id, manager, start_date, end_date, reason, leave_type, leave_requests, user_leave_balance)
                    close_modal(payload['view']['id'])

                print('user_leave_balance in 167', user_leave_balance)
                # update_message(payload['response_url'], f"Leave request submitted. Summary: {leave_summary}")

            elif action_id == 'leave_statistics':
                send_leave_statistics(user_id, trigger_id)
            elif action_id == 'team_member_leave':
                print('i am in this action')
                username = user_mapping.get(user_id, None)
                manager = manager_mapping.get(username, None)

                if manager:
                    team_members = [uid for uid, uname in user_mapping.items() if manager_mapping.get(uname) == manager]
                    leave_data = {uid: leave_requests.get(uid, {'details': []})['details'] for uid in team_members}
                    print("Leave data:", leave_data)  # Debugging log

                
            elif action_id == 'filter_button':
                state = payload['view']['state']['values']
                selected_user_id = state['user_block']['user_select']['selected_option']['value']
                
                print('payload in 110', payload)

                filtered_leave_statistics = filter_leave_statistics(selected_user_id)
                print('filtered leave statistics', filtered_leave_statistics)
                update_modal(payload['view']['id'], filtered_leave_statistics)

    
            elif action_id in ['approve_request', 'reject_request']:
                print('payload in line 108', payload)
                action_data = json.loads(payload['actions'][0]['value'])
                print('action_data', action_data)
                original_user_id = action_data['user_id']
                status = action_data['status']

                original_username = user_mapping.get(original_user_id, 'Unknown User')
                manager_name = manager_mapping.get(original_username, 'Unknown Manager')

                manager_id = next((key for key, value in user_mapping.items() if value == manager_name), None)
                print('leave requests in 227 views', leave_requests)
                if original_user_id in user_leave_constraints:
                    user_leave_balance = user_leave_constraints[original_user_id]
                else:
                    user_leave_balance = leave_constraints_template.copy()
                    user_leave_constraints[original_user_id] = user_leave_balance

                handle_manager_response(original_user_id, status, manager_channel_id, manager_id, user_channel_id, leave_requests, user_leave_balance)

            return JsonResponse({'status': 'Action processed'})
        
        elif 'view' in payload:
            view_id = payload['view']['id']
            user_id = payload['user']['id']
            state = payload['view']['state']['values']
            
            channel_id = payload['view'].get('private_metadata', None)

            print('payload view state', payload['view']['state'])

            if 'start_date_block' in state and 'end_date_block' in state and 'reason_block' in state:
                start_date = state['start_date_block']['start_date']['selected_date']
                end_date = state['end_date_block']['end_date']['selected_date']
                reason = state['reason_block']['leave_reason']['value']

                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                leave_days = (end_date_obj - start_date_obj).days + 1

                username = user_mapping.get(user_id, 'Unknown User')
                manager = manager_mapping.get(username, 'Unknown Manager')

                if user_id not in leave_requests:
                    leave_requests[user_id] = {
                        'leave_taken': 0,
                        'details': []
                    }
                leave_requests[user_id]['leave_taken'] += leave_days
                leave_requests[user_id]['details'].append({
                    'start_date': start_date,
                    'end_date': end_date,
                    'leave_days': leave_days,
                    'status': 'Pending',
                    'reason': reason
                })

                send_leave_summary(user_id, manager, start_date, end_date, reason, channel_id,leave_requests, user_leave_balance)
                update_message(payload['response_url'], f"Leave request submitted. Days requested: {leave_days}")

            return JsonResponse({'status': 'View submission processed'})
    
    return HttpResponse(status=405)
            
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()  
    print(response.json())

