import streamlit as st
from openai import OpenAI
import os
import pandas as pd
import json
import io

DEFAULT_EMAIL_PROMPT = """
You are an expert email copywriter specializing in personalized outreach for a professional cohort-based course. 
Your emails should be:
- Warm and engaging
- Personalized based on the individual's motivation and background
- Professional yet conversational
- Highlighting the potential value of the course for their specific career goals
"""

def validate_api_key(api_key):
    try:
        client = OpenAI(api_key=api_key)
        client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello, can you confirm this API key is working?"}],
            max_tokens=10,
        )
        return True
    except Exception as e:
        st.error(f"Error communicating with OpenAI: {str(e)}")
        return False

def get_openai_response(messages, api_key):
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=4000,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error communicating with OpenAI: {str(e)}")
        return None

def process_leads(df):
    leads_data = df.to_dict("records")
    formatted_leads = json.dumps(leads_data, indent=2)

    prompt = f"""
    You are a marketing genius that works for online cohort-based course instructors. You are trained to find and score leads based on user engagement across various channels. Your task is to generate a lead scoring table that identifies high-potential candidates for the course. 

Here are the scoring criteria you should consider:  
- Channel Presence: Max 50 points  
- Professional Experience: Max 50 points  
- Career Motivation: Max 30 points  
- Geographic Relevance: Max 30 points  

The scoring breakdown is as follows:  
- Cross-Channel Presence: 50 points  
- Product Management/Tech Experience: 60 points  
- Clear Career Goal Alignment: 40 points  
- Location Relevance: 40 points  

You will analyze the provided lead data, calculate lead scores based on the scoring methodology, and generate a table with the specified output format. Ensure that the user with the highest lead score appears at the top of the table. For each lead, provide a clear rationale for their score. 

Make sure to output the information in a table format with the following columns:  
| Full Name | Preferred Name | Email | Lead Score | Reason | LinkedIn | Motivation |

It is crucial that you process and include ALL leads from the input data. The current lead count is: {len(leads_data)}. Ensure the following:  
- Verify data completeness  
- Ensure professional and ethical lead scoring  
- No fabricated information  
- Respect data privacy  

Your output should strictly adhere to the table format without any additional commentary or information.

<Lead Data>
{formatted_leads}
</Lead Data>
"""
    return prompt

def parse_lead_data(input_text):
    try:
        data = json.loads(input_text)
        return data if isinstance(data, list) else [data]
    except:
        try:
            df = pd.read_csv(io.StringIO(input_text), sep=None, engine='python')
            return df.to_dict('records')
        except:
            lines = [line.strip() for line in input_text.split('\n') if line.strip()]
            return [{'input': line} for line in lines]

def generate_personalized_emails(leads_data, api_key, email_system_prompt):
    messages = [
        {"role": "system", "content": email_system_prompt},
        {"role": "user", "content": f"Generate personalized emails for:\n{json.dumps(leads_data, indent=2)}"}
    ]
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=4000,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating emails: {str(e)}")
        return None

def main():
    st.set_page_config(
        page_title="Lead Generation Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    if 'email_system_prompt' not in st.session_state:
        st.session_state['email_system_prompt'] = DEFAULT_EMAIL_PROMPT
    
    if 'show_debug' not in st.session_state:
        st.session_state['show_debug'] = False

    with st.sidebar:
        st.title("🚀 Lead Generation Tool")
        api_key = st.text_input("Enter OpenAI API Key", type="password")

        if st.button("Validate API Key"):
            if api_key:
                if validate_api_key(api_key):
                    st.session_state["api_key_valid"] = True
                    st.session_state["api_key"] = api_key
                    st.success("🎉 API Key validated successfully!")
                else:
                    st.session_state["api_key_valid"] = False
                    st.session_state["api_key"] = None

        st.write("### 🛠 Tools")
        page = st.radio("Select a Tool", ["Generate Leads", "Generate Emails"])

    if page == "Generate Leads":
        st.header("🔍 Lead Generation")

        if not st.session_state.get("api_key_valid", False):
            st.warning("Please validate your API key first 🔑.")
        else:
            uploaded_file = st.file_uploader(
                "Upload your file", type=["csv", "xlsx", "txt"]
            )

            if uploaded_file is not None:
                try:
                    if uploaded_file.type == "text/csv":
                        df = pd.read_csv(uploaded_file)
                    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                        df = pd.read_excel(uploaded_file)
                    else:
                        df = pd.read_csv(uploaded_file, sep="\t")

                    st.success(f"💯 File uploaded successfully! Found {len(df)} leads.")

                    if st.button("Generate Leads 🖱️"):
                        with st.spinner(f"Analyzing {len(df)} leads...🤔"):
                            prompt = process_leads(df)
                            messages = [
                                {"role": "system", "content": "You are a lead scoring expert specializing in analyzing potential course participants."},
                                {"role": "user", "content": prompt},
                            ]
                            response = get_openai_response(messages, st.session_state["api_key"])

                            if response:
                                st.success(f"Lead analysis completed for {len(df)} leads! 📂")
                                st.markdown("### Lead Analysis Results")
                                st.markdown(response)
                                st.markdown("---")
                                st.download_button(
                                    label="Download Analysis",
                                    data=response,
                                    file_name="lead_analysis.md",
                                    mime="text/markdown",
                                )
                            else:
                                st.error("Failed to analyze leads. ❌")
                except Exception as e:
                    st.error(f"Error processing file: {str(e)} ❌")

    elif page == "Generate Emails":
        st.header("✉️ Email Generation Tool")
        if not st.session_state.get("api_key_valid", False):
            st.warning("Please validate your API key first 🔑")
        else:
            col1, col2 = st.columns([1, 6])
            with col1:
                if st.button("Debug 🔧"):
                    st.session_state['show_debug'] = not st.session_state['show_debug']
            
            if st.session_state['show_debug']:
                temp_prompt = st.text_area(
                    "Email Generation Prompt",
                    value=st.session_state['email_system_prompt'],
                    height=200
                )
                if st.button("Save Changes 💾"):
                    st.session_state['email_system_prompt'] = temp_prompt
                    st.success("Prompt updated successfully!")

            lead_input = st.text_area(
                "Enter lead data (JSON, CSV, or free text)",
                height=300,
                placeholder="Enter lead information in any format..."
            )

            if st.button("Generate Emails 🖱️"):
                if lead_input.strip():
                    with st.spinner("Generating emails...🤔"):
                        leads_data = parse_lead_data(lead_input)
                        emails = generate_personalized_emails(
                            leads_data,
                            st.session_state["api_key"],
                            st.session_state['email_system_prompt']
                        )

                        if emails:
                            st.success("Email templates generated!")
                            st.markdown("### Generated Email Templates")
                            st.markdown(emails)
                            st.markdown('---')
                            st.download_button(
                                label="Download Email Templates",
                                data=emails,
                                file_name="email_templates.md",
                                mime="text/markdown",
                            )
                else:
                    st.error("Please enter lead data ❌")

if __name__ == "__main__":
    if "api_key_valid" not in st.session_state:
        st.session_state["api_key_valid"] = False
    main()