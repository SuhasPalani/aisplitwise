import google.generativeai as genai
from core.config import settings
import json
import re

genai.configure(api_key=settings.GEMINI_API_KEY)

async def get_smart_split(expense_data: dict, group_members: list) -> dict:
    model = genai.GenerativeModel('gemini-pro')

    prompt = f"""
    You are an intelligent expense splitter. Your task is to suggest a fair split of an expense among participants.
    
    Expense Details:
    Description: {expense_data['description']}
    Total Amount: {expense_data['amount']}
    Paid By: {expense_data['paid_by']}
    Participants (who benefited from/are part of this expense): {', '.join(expense_data['participants'])}
    All available group members (for context, participants are a subset): {', '.join(group_members)}

    Provide a dictionary where keys are participant usernames and values are the amounts they owe or are responsible for, rounding to 2 decimal places. The sum of the split amounts MUST equal the total amount.
    
    Example Output:
    {{
      "john": 10.50,
      "alice": 10.50,
      "bob": 21.00
    }}

    Consider common sense splits:
    - If no specific instructions, split equally among participants.
    - If the description implies one person took more/less, suggest a reasonable unequal split.
    - If someone is explicitly excluded or didn't participate, they should not be in the split.

    Provide only the JSON dictionary as output, no extra text or explanation.
    """
    
    try:
        response = model.generate_content(prompt)
        # Attempt to extract JSON from potentially wrapped response
        response_text = response.text.strip()
        
        # Regex to find JSON object, even if it's wrapped in markdown or other text
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(0)
            split_suggestion = json.loads(json_str)

            # Basic validation of the split
            total_suggested = sum(split_suggestion.values())
            if abs(total_suggested - expense_data['amount']) > 0.02: # Allow for slight float discrepancies
                print(f"Warning: AI suggested split total ({total_suggested}) does not match expense amount ({expense_data['amount']}). Adjusting to proportional split.")
                # Fallback to equal split if AI's sum is too far off
                num_participants = len(expense_data['participants'])
                if num_participants > 0:
                    equal_share = round(expense_data['amount'] / num_participants, 2)
                    adjusted_split = {p: equal_share for p in expense_data['participants']}
                    # Adjust last participant for perfect sum
                    if adjusted_split:
                        last_participant = expense_data['participants'][-1]
                        adjusted_split[last_participant] += expense_data['amount'] - sum(adjusted_split.values())
                        adjusted_split[last_participant] = round(adjusted_split[last_participant], 2)
                    return adjusted_split
                else:
                    return {} # No participants, no split

            # Ensure all suggested participants are actual participants and filter out others
            final_split = {p: round(split_suggestion.get(p, 0.0), 2) for p in expense_data['participants']}
            
            # Recalculate sum to ensure it matches exactly due to rounding
            current_sum = sum(final_split.values())
            if abs(current_sum - expense_data['amount']) > 0.01:
                # Distribute the small difference to one participant
                if final_split:
                    diff = expense_data['amount'] - current_sum
                    first_participant = list(final_split.keys())[0]
                    final_split[first_participant] += diff
                    final_split[first_participant] = round(final_split[first_participant], 2)

            return final_split

        else:
            print(f"Error: Could not extract JSON from AI response: {response_text}")
            # Fallback to equal split if AI response is unparseable
            num_participants = len(expense_data['participants'])
            if num_participants > 0:
                equal_share = round(expense_data['amount'] / num_participants, 2)
                adjusted_split = {p: equal_share for p in expense_data['participants']}
                if adjusted_split:
                    last_participant = expense_data['participants'][-1]
                    adjusted_split[last_participant] += expense_data['amount'] - sum(adjusted_split.values())
                    adjusted_split[last_participant] = round(adjusted_split[last_participant], 2)
                return adjusted_split
            else:
                return {}

    except Exception as e:
        print(f"Error calling Gemini API or parsing response: {e}")
        # Fallback to equal split on error
        num_participants = len(expense_data['participants'])
        if num_participants > 0:
            equal_share = round(expense_data['amount'] / num_participants, 2)
            adjusted_split = {p: equal_share for p in expense_data['participants']}
            if adjusted_split:
                last_participant = expense_data['participants'][-1]
                adjusted_split[last_participant] += expense_data['amount'] - sum(adjusted_split.values())
                adjusted_split[last_participant] = round(adjusted_split[last_participant], 2)
            return adjusted_split
        else:
            return {}