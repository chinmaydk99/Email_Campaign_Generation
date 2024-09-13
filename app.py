import streamlit as st
import asyncio
from models import CampaignInput, Product, EmailCampaignState
from graph import create_email_campaign_graph
import json
import base64
from config import TONES, PRODUCT_CATEGORIES
import streamlit.components.v1 as components
import subprocess
import os

# Streamlit configuration
st.set_page_config(page_title="Email Campaign Generator", layout="wide")

# Custom CSS for better styling
st.markdown("""
<style>
    .main { padding: 2rem; }
    .stButton>button { width: 100%; }
    .stProgress>div>div>div { background-color: #4CAF50; }
    .product-box {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .variant-box {
        background-color: #e6f3ff;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Email Campaign Generator")
st.markdown("Generate compelling email campaigns with AI-powered content creation.")

# Specify the directory and batch file name for image generation
batch_file_directory = './Fooocus_win64_2-5-0'
batch_file_name = 'run.bat'

def run_batch_file():
    try:
        # Change to the specified directory
        os.chdir(batch_file_directory)
        # Run the batch file and capture the output
        process = subprocess.Popen(batch_file_name, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        return stdout.decode('utf-8'), stderr.decode('utf-8')
    except Exception as e:
        return "", str(e)

# Image Generation Button at the top
if st.button("Proceed to Image Generation"):
    with st.spinner("Running the batch file..."):
        try:
            stdout, stderr = run_batch_file()
            if stdout:
                st.success("Batch file executed successfully!")
                st.code(stdout)
            if stderr:
                st.error("Errors occurred while running the batch file:")
                st.code(stderr)
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

st.sidebar.header("Campaign Configuration")

segment_name = st.sidebar.text_input("Target Segment Name")
campaign_type = st.sidebar.text_input("Enter the Campaign Type")
num_variants = st.sidebar.slider("Number of Variants", 1, 5, 2)

st.sidebar.subheader("Products")
num_products = st.sidebar.number_input("Number of Products", 1, 5, 2)

products = []
for i in range(num_products):
    st.sidebar.markdown(f"<div class='product-box'>", unsafe_allow_html=True)
    st.sidebar.markdown(f"### Product {i+1}")
    
    product_category = st.sidebar.selectbox(
        f"Product {i+1} Category", 
        options=list(PRODUCT_CATEGORIES.keys()),
        key=f"product_category_{i}"
    )
    
    if product_category:
        product_name = st.sidebar.selectbox(
            f"Product {i+1} Name",
            options=PRODUCT_CATEGORIES[product_category]['options'],
            key=f"product_name_{i}"
        )
        
        if product_name:
            products.append(Product(name=product_name, category=product_category))
    
    st.sidebar.markdown("</div>", unsafe_allow_html=True)

def get_download_link(content, filename, text):
    b64 = base64.b64encode(content.encode()).decode()
    return f'<a href="data:file/txt;base64,{b64}" download="{filename}">{text}</a>'

def format_text_content(variant):
    content = variant['content']
    formatted_text = f"""Subject Line: {content.subject_line}

Pre-header: {content.pre_header}

Body:
{content.body}
"""
    return formatted_text

async def run_email_campaign(campaign_input: CampaignInput):
    initial_state = EmailCampaignState(
        products=campaign_input.products,
        campaignInfo=campaign_input,
        variants=[],
        qa_feedback=None,
        html_email=None,
        current_tone= TONES[0]
    )

    email_campaign_graph = create_email_campaign_graph()

    config = {
        "configurable": {"thread_id": "email-campaign-thread"},
        "recursion_limit": 500
    }

    progress_bar = st.progress(0)
    status_text = st.empty()

    async def process_stream(stream):
        steps = ["planner", "researcher", "subject line writer", "preheader writer", "body writer", "email variant aggregator", "quality assurance agent", "html agent", "add approved variant"]
        total_steps = max(len(steps) * campaign_input.num_variants * len(TONES), 1)
        current_step = 0

        async for event in stream:
            step_name = list(event.keys())[0]
            step_data = event[step_name]

            current_step += 1
            progress = min(int(current_step / total_steps * 100), 100)
            progress_bar.progress(progress)

            status_text.text(f"Step: {step_name.capitalize()}")

            if step_name == "add approved variant":
                st.success(f"Variant {len(event[step_name].get('variants', []))} completed!")

            await asyncio.sleep(0.1)

    await process_stream(email_campaign_graph.astream(initial_state, config=config))

    final_state = email_campaign_graph.get_state(config=config)[0]
    return final_state

if 'show_html' not in st.session_state:
    st.session_state.show_html = {}

if st.sidebar.button("Generate Campaign"):
    if segment_name and campaign_type and products and all(p.name for p in products):
        with st.spinner("Generating your email campaign..."):
            campaign_input = CampaignInput(
                segment_name=segment_name,
                campaign_type=campaign_type,
                products=products,
                num_variants=num_variants
            )
            final_state = asyncio.run(run_email_campaign(campaign_input))

        st.success("Email Campaign Generation Complete!")

        st.header("Campaign Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Campaign Type", final_state['campaignInfo'].campaign_type)
        col2.metric("Target Segment", final_state['campaignInfo'].segment_name)
        col3.metric("Number of Variants", len(final_state['variants']))

        st.subheader("Featured Products")
        for product in final_state['products']:
            st.markdown(f"- **{product.name}** ({product.category})")

        with st.expander("Campaign Plan"):
            if 'campaign_plan' in final_state:
                st.text_area("Campaign Plan", final_state['campaign_plan'], height=300)
                download_link = get_download_link(final_state['campaign_plan'], "campaign_plan.txt", "Download Campaign Plan")
                st.markdown(download_link, unsafe_allow_html=True)
            else:
                st.warning("Campaign plan not available")

        with st.expander("Research Findings"):
            if 'research_findings' in final_state:
                for research in final_state['research_findings']:
                    st.subheader(f"Research for {research.product_name}")
                    st.markdown("#### Product Research Summary")
                    st.text_area(f"Product Research Summary - {research.product_name}", research.research_summary, height=200)
                    st.markdown("#### Offer Summary")
                    st.text_area(f"Offer Summary - {research.product_name}", research.offer_summary, height=200)
                
                all_research = "\n\n".join([f"Research for {r.product_name}\n\nProduct Research Summary:\n{r.research_summary}\n\nOffer Summary:\n{r.offer_summary}" for r in final_state['research_findings']])
                download_link = get_download_link(all_research, "research_findings.txt", "Download All Research Findings")
                st.markdown(download_link, unsafe_allow_html=True)
            else:
                st.warning("Research findings not available")

        st.header("Email Variants")

        all_variants = final_state['variants']
        grouped_variants = {}

        for variant in all_variants:
            tone = variant['tone']
            if tone not in grouped_variants:
                grouped_variants[tone] = []
            grouped_variants[tone].append(variant)

        for tone in TONES:
            tone_variants = grouped_variants.get(tone, [])
            
            if tone_variants:
                st.subheader(f"Tone: {tone}")
                
                for i, variant in enumerate(tone_variants, 1):
                    with st.expander(f"Variant {i}"):
                        st.markdown(f"### Subject Line\n{variant['content'].subject_line}")
                        st.markdown(f"### Pre-header\n{variant['content'].pre_header}")
                        st.markdown("### Body")
                        st.text_area("", variant['content'].body, height=200)
                        
                        formatted_text = format_text_content(variant)
                        
                        text_download_link = get_download_link(formatted_text, f"{tone}_variant_{i}_content.txt", "Download Formatted Text")
                        html_download_link = get_download_link(variant['html_email'], f"{tone}_variant_{i}.html", "Download HTML")
                        
                        st.markdown(text_download_link, unsafe_allow_html=True)
                        st.markdown(html_download_link, unsafe_allow_html=True)
                        
                        if st.button(f"View HTML for {tone} Variant {i}", key=f"{tone}_{i}_html"):
                            st.components.v1.html(variant['html_email'], height=600, scrolling=True)
            else:
                st.warning(f"No variants generated for tone: {tone}")

        st.subheader("Debug Information")
        st.write("Total number of variants:", len(final_state['variants']))
        for variant in final_state['variants']:
            st.write(f"Tone: {variant['tone']}")

        all_variants_text = "\n\n".join([format_text_content(variant) for variant in final_state['variants']])
        all_variants_html = "\n\n".join([variant['html_email'] for variant in final_state['variants']])
        
        st.header("Download All Variants")
        st.markdown(get_download_link(all_variants_text, "all_variants_content.txt", "Download All Formatted Text"), unsafe_allow_html=True)
        st.markdown(get_download_link(all_variants_html, "all_variants.html", "Download All HTML"), unsafe_allow_html=True)

    else:
        st.warning("Please fill in all the required fields before generating the campaign.")

st.sidebar.markdown("---")
st.sidebar.info("This tool uses AI to generate email campaigns based on your input. The generated content is a starting point and may require further refinement.")