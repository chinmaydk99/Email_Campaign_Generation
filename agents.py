from langchain.prompts import ChatPromptTemplate
from models import EmailCampaignState, ProductResearch, QAFeedback, SubjectLine, Preheader, EmailVariant, EmailBody
import instructor
from openai import OpenAI
from langgraph.prebuilt import ToolInvocation
import chromadb
import json
from tenacity import retry, wait_fixed, stop_after_attempt
from config import llm, MODEL, tool_executor, TONES
from utils import retry_with_backoff, generate_html_body
from database import setup_chromadb, query_database



@retry_with_backoff()
async def planner_agent(state: EmailCampaignState):
    products = ', '.join([p.name for p in state['products']])

    try:
        prompt = ChatPromptTemplate.from_template("""
        You are an expert email marketing campaign planner. Given the following campaign information,
        create a comprehensive, high-level plan for the email campaign featuring multiple products.

        Campaign Info:
        {campaign_info}

        Products:
        {products}

        Provide a detailed, structured plan including:
        1. Campaign goals and objectives (be specific and measurable)
        2. Target audience analysis and segmentation strategy
        3. Key messaging points and unique value propositions for each product
        4. Personalization strategy and tactics
        5. Suggested email structure and content outline, considering multiple products
        6. Timing and frequency recommendations
        7. Success metrics and KPIs
        8. Potential challenges and mitigation strategies
        9. Integration with other marketing channels (if applicable)
        10. Compliance considerations and best practices

        Additionally, incorporate these best practices:
        - Include offers for each product, as messages with offers perform better
        - Focus on targeted offers as they perform best of all
        - Use customer names in subject lines
        - State offer value in preheader
        - Thank existing users in email body (for reactivation campaigns)
        - For existing customers, focus on upgrade benefits
        - Include product/family names in subject line
        - Use inquisitive questions to engage readers
        - Express ownership appreciation for reactivation (existing customers)
        - Use FOMO (Fear of Missing Out) language rather than simple urgency

        Your plan should be thorough, actionable, and aligned with industry best practices for email marketing featuring multiple products.
        """)

        response = await llm.ainvoke(
            prompt.format(campaign_info=state['campaignInfo'],
                          products=products)
        )

        state['campaign_plan'] = response.content
        return state

    except Exception as e:
        print(f"Error in planner: {str(e)}")
        raise

@retry_with_backoff()
async def researcher_agent(state: EmailCampaignState):
    try:
        product_collection, promotions_collection = setup_chromadb()
        research_findings = []

        for product in state["products"]:
            queries = [
                f"What are the key features of the {product.name}?",
            ]

            research_data = ""
            for query in queries:
                product_results = query_database(product_collection, query)
                if product_results['documents'][0]:
                    research_data += f"\nQuery: {query}\n"
                    research_data += f"Result: {product_results['documents'][0][0]}\n"

            product_research_prompt = ChatPromptTemplate.from_template("""
            You are a marketing specialist for Samsung's email campaigns. Analyze the following research data for {product_name} in the {product_category} category:

            {research_data}

            Create a marketing-focused summary that includes:

            1. Key Product Features:
               - List the main features and innovations highlighted in Samsung's marketing
               - Identify any standout technologies or capabilities, especially AI-related features

            2. Galaxy AI Integration: (if applicable)
               - Describe how Galaxy AI is integrated into this product (if applicable)
               - Explain the benefits and enhancements provided by AI features (if applicable)

            3. Marketing Language:
               - Note specific phrases or slogans used to describe the product and its AI capabilities
               - Identify any emotional appeals or lifestyle benefits emphasized

            4. Offers and Incentives:
               - Summarize any special offers, pre-order benefits, or promotions mentioned

            5. Competitive Advantages:
               - Highlight how Samsung positions this product against competitors, especially in terms of AI features

            6. Email Marketing Suggestions:
               - Propose 3-5 key points to emphasize in email campaigns, incorporating both product features and relevant AI capabilities
               - Suggest attention-grabbing subject line ideas based on the product's highlights and AI features

            Focus on capturing Samsung's official marketing angle for {product_name}, integrating Galaxy AI information where relevant. Use the actual language and emphasis found in their promotional material where possible.
            """)

            product_research_response = await llm.ainvoke(
                product_research_prompt.format(
                    product_name=product.name,
                    product_category=product.category,
                    research_data=research_data
                )
            )

            query = f"Can you fetch me the pricing, deals and promotions information for {product.name}?"

            offers_pricing_data = ""

            promotions_results = query_database(promotions_collection, query)
            if promotions_results['documents'][0]:
                offers_pricing_data += f"\nQuery: {query}\n"
                offers_pricing_data += f"Result: {promotions_results['documents'][0][0]}\n"

            promotions_prompt = ChatPromptTemplate.from_template("""
            You are a pricing and promotions specialist for Samsung's email campaigns. Analyze the following offers, pricing, and promotional information for {product_name}:

            {offers_pricing_data}

            Create a concise, marketing-focused summary that includes:

            1. Pricing(important):
                - Current prices for different models/storage options
                - Any discounts or savings from original prices
                - Financing options (e.g., monthly payments, APR)

            2. Promotional Offers:
                - Trade-in credits or special trade-in programs
                - Bundle deals (e.g., discounts on accessories)
                - Limited-time offers or exclusive deals

            3. Additional Benefits:
                - Included services (e.g., Samsung Care+)
                - Partner offers or free trials

            4. Availability and Delivery:
                - Expected delivery dates or in-store pickup options

            5. Key Selling Points:
                - Highlight the best value propositions (e.g., biggest savings, most popular deal)
                - Any unique or standout offers compared to competitors

            6. Email Marketing Suggestions:
                - Propose 3 attention-grabbing subject line ideas focusing on the best offers
                - Suggest 3-5 key points to emphasize in email campaigns related to pricing and promotions

            Keep the summary concise and focused on the most compelling offers and deals. Use actual numbers and specific details where possible. The goal is to provide clear, persuasive information that can be easily incorporated into email marketing campaigns.
            """)

            promotions_response = await llm.ainvoke(
                promotions_prompt.format(
                    product_name=product.name,
                    product_category=product.category,
                    offers_pricing_data=offers_pricing_data
                )
            )

            research_findings.append(ProductResearch(
                product_name=product.name,
                research_summary= product_research_response.content.strip(),
                offer_summary= promotions_response.content.strip()
            ))

        state["research_findings"] = research_findings

    except Exception as e:
        print(f"Error in researcher: {str(e)}")
        raise

    return state


@retry_with_backoff()
async def subject_line_writer_agent(state: EmailCampaignState):
    try:
        product_research, offer_research =  '', ''
        for research in state['research_findings']:
            product_research += f"\n{research.product_name}: {research.research_summary}"
            offer_research += f"\n{research.product_name}: {research.offer_summary}"

        prompt = ChatPromptTemplate.from_template("""
        You are an expert email subject line writer for Samsung, writing in a {tone} tone.
        Campaign Type: {campaign_type}
        Target Segment: {segment_name}
        Products: {products}

        Guidelines:
        - Maximum 50 characters
        - You must include the product name in the subject line (from {products})
        - Include [NAME] placeholder
        - Highlight a key feature(from {product_research})
        - Tailor it based on the campaign type{campaign_type} and/or target segment{segment_name}
        - Create FOMO or use an inquisitive question
        - Use an emoji if appropriate
        - Ensure the subject line reflects the {tone} tone

        Provide the subject line in the following JSON format:
        {{
          "subject": "subject line text"
        }}

        Ensure that the subject line doesn't exceed 50 characters. This is non-negotiable.
        """)

        client = instructor.from_openai(
            OpenAI(base_url="http://localhost:11434/v1", api_key="ollama"),
            mode=instructor.Mode.JSON
        )

        resp = client.chat.completions.create(
            model= MODEL,
            messages=[
                {"role": "system", "content": "You are an expert email subject line writer for Samsung."},
                {"role": "user", "content": prompt.format(
                    campaign_type=state['campaignInfo'].campaign_type,
                    segment_name=state['campaignInfo'].segment_name,
                    products=', '.join([p.name for p in state['products']]),
                    product_research=product_research,
                    offer_research=offer_research,
                    tone = state['current_tone']
                )}
            ],
            response_model=SubjectLine
        )

        state['current_subject_line'] = json.dumps(resp.model_dump())

    except Exception as e:
        print(f"Error in subject line writer: {str(e)}")
        raise

    return state

@retry_with_backoff()
async def preheader_writer_agent(state: EmailCampaignState):
    try:
        product_research, offer_research =  '', ''
        for research in state['research_findings']:
            product_research += f"\n{research.product_name}: {research.research_summary}"
            offer_research += f"\n{research.product_name}: {research.offer_summary}"

        prompt = ChatPromptTemplate.from_template("""
        You are an expert email pre-header writer for Samsung, writing in a {tone} tone.
        Campaign Type: {campaign_type}
        Target Segment: {segment_name}
        Products: {products}
        Subject Line: {subject_line}

        Guidelines:
        - 50-100 characters
        - Expand on the subject line. Not literally but add information not present in the subject line
        - Highlight a key offer(from {offer_research}) not mentioned in the subject line
        - Ensure it complements the subject line and entices further reading

        Provide the preheader in the following JSON format:
        {{
          "preheader": "preheader text"
        }}

        Ensure that the pre-header doesn't exceed 100 characters. This is non-negotiable.
        """)

        client = instructor.from_openai(
            OpenAI(base_url="http://localhost:11434/v1", api_key="ollama"),
            mode=instructor.Mode.JSON,
        )

        resp = client.chat.completions.create(
            model= MODEL,
            messages=[
                {"role": "system", "content": "You are an expert email preheader writer for Samsung."},
                {"role": "user", "content": prompt.format(
                    campaign_type=state['campaignInfo'].campaign_type,
                    segment_name=state['campaignInfo'].segment_name,
                    products=', '.join([p.name for p in state['products']]),
                    subject_line=json.loads(state['current_subject_line'])['subject'],
                    product_research=product_research,
                    offer_research=offer_research,
                    tone = state['current_tone']
                )}
            ],
            response_model=Preheader,
        )

        state['current_preheader'] = json.dumps(resp.model_dump())

    except Exception as e:
        print(f"Error in preheader writer: {str(e)}")
        raise

    return state

@retry_with_backoff()
async def body_writer_agent(state: EmailCampaignState):
    try:
        product_research, offer_research =  '', ''
        for research in state['research_findings']:
            product_research += f"\n{research.product_name}: {research.research_summary}"
            offer_research += f"\n{research.product_name}: {research.offer_summary}"

        prompt = ChatPromptTemplate.from_template("""
        You are an expert email body writer for Samsung, writing in a {tone} tone.
        Campaign Type: {campaign_type}
        Target Segment: {segment_name}


        Start with a personalized greeting using [NAME] (max 50 characters)

        For each product({products}), create feature modules based on the following guidelines:

        Guidelines:
        - For each product within {products}, create 3 modules, each representing a key feature of the product from {product_research}:
          * The module title (max 50 characters) MUST be a key feature directly from the {product_research}
          * If Galaxy AI is mentioned in the product research, it MUST be one of the modules
          * Include a single line description of the module title which should expand on the feature, taken directly from {product_research}. This should be less than 10 words
          * CTA for each module (max 30 characters).  The CTA text can vary and should be enticing but make them all point to https://www.samsung.com/us/
        - Include a main CTA (max 50 characters) and a main CTA link
        - Ensure the content aligns with the {campaign_type} and appeals to the {segment_name}

        Provide the email body in the following JSON format:
        {{
          "product_modules": [
            {{
              "title": "Key Feature Title",
              "content": "Feature description and benefits",
              "cta_text": "Optional CTA text",
              "cta_link": "Optional CTA link"
            }},
            ...
          ],
          "main_cta": "Main call-to-action text",
          "main_cta_link": "Main CTA link"
        }}

        Ensure that the total length of all text (excluding links) doesn't exceed 850 characters.
        """)

        client = instructor.from_openai(
            OpenAI(base_url="http://localhost:11434/v1", api_key="ollama"),
            mode=instructor.Mode.JSON,
        )

        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an expert email body writer for product campaigns."},
                {"role": "user", "content": prompt.format(
                    campaign_type=state['campaignInfo'].campaign_type,
                    segment_name=state['campaignInfo'].segment_name,
                    products=', '.join([p.name for p in state['products']]),
                    product_research=product_research,
                    offer_research=offer_research,
                    tone = state['current_tone']
                )}
            ],
            response_model=EmailBody
        )

        state['current_body'] = json.dumps(resp.model_dump())
        print(state["current_body"])

    except Exception as e:
        print(f"Error in body writer: {str(e)}")
        raise

    return state


@retry_with_backoff()
async def email_variant_aggregator(state: EmailCampaignState):
    try:
        subject_line = json.loads(state['current_subject_line'])['subject']
        preheader = json.loads(state['current_preheader'])['preheader']
        body = json.loads(state['current_body'])

        email_body = ""

        for module in body["product_modules"]:
            email_body += f"{module['title']}\n{module['content']}\n{module['cta_text']}: {module['cta_link']} \n\n"

        email_body += f"{body['main_cta']}\n{body['main_cta_link']}\n"

        variant = EmailVariant(
            subject_line=subject_line,
            pre_header=preheader,
            body=email_body
        )

        state['current_variant'] = variant

        state['current_subject_line'] = None
        state['current_preheader'] = None


    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in email variant aggregator: {str(e)}")
        raise
    except KeyError as e:
        print(f"Missing key in JSON structure in email variant aggregator: {str(e)}")
        raise
    except Exception as e:
        print(f"Error in email variant aggregator: {str(e)}")
        raise

    return state


@retry_with_backoff()
async def quality_assurance_agent(state: EmailCampaignState):
    try:
        prompt = ChatPromptTemplate.from_template("""
        You are an expert quality assurance specialist for email marketing campaigns. Your task is to review the email variant and provide detailed feedback to ensure it meets all quality standards and aligns with the campaign objectives.

        Campaign Type: {campaign_type}
        Target Segment: {segment_name}
        Email Variant to Review:
        Subject Line: {subject_line}
        Pre-header: {pre_header}
        Body: {body}

        Conduct a thorough review of the email variant, considering the following aspects:
        1. Alignment with Campaign Objectives and Type
        2. Target Audience Appropriateness
        3. Subject Line and Preheader
        4. Content Quality and Relevance
        5. Personalization
        6. Call-to-Action (CTA)
        7. Product Presentation
        8. Grammar and Spelling
        9. Product Inclusivity
        10. Overall Effectiveness

        Provide your feedback in the following JSON format:

        {{
            "overall_rating": <rating (1-10)>,
            "strengths": ["<strength 1>", "<strength 2>", ...],
            "weaknesses": ["<weakness 1>", "<weakness 2>", ...],
            "suggestions": ["<suggestion 1>", "<suggestion 2>", ...],
            "needs_revision": <boolean>
        }}

        Ensure your feedback is detailed, constructive, and actionable. Set "needs_revision" to true only if there are critical issues that significantly impact the effectiveness of the email for the {campaign_type} or {segment_name}. Minor improvements should be suggested without requiring a full revision. The overall rating should be 8 or higher for approval unless there are major issues.
        """)

        client = instructor.from_openai(
            OpenAI(base_url="http://localhost:11434/v1", api_key="ollama"),
            mode=instructor.Mode.JSON,
        )

        qa_response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an expert quality assurance specialist for email marketing campaigns."},
                {"role": "user", "content": prompt.format(
                    campaign_type=state['campaignInfo'].campaign_type,
                    segment_name=state['campaignInfo'].segment_name,
                    subject_line=state['current_variant'].subject_line,
                    pre_header=state['current_variant'].pre_header,
                    body=state['current_variant'].body,
                    products = ', '.join([product.name for product in state['products']])
                )}
            ],
            response_model=QAFeedback
        )

        feedback = qa_response.model_dump()
        feedback['is_first_review'] = state.get('qa_feedback') is None

        state['qa_feedback'] = feedback

    except Exception as e:
        print(f"Error in quality assurance agent: {str(e)}")
        raise

    return state




@retry_with_backoff()
async def html_agent(state: EmailCampaignState):
    try:
        variant = state['current_variant']
        body_content = state['current_body']

        body_html = generate_html_body(body_content)

        html_template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{variant.subject_line}</title>
            <style type="text/css">
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                    font-size: 16px;
                    line-height: 1.6;
                    color: #333333;
                }}
                table {{
                    border-collapse: collapse;
                }}
                img {{
                    border: 0;
                    display: block;
                }}
                .preheader {{
                    display: none !important;
                }}
                @media only screen and (max-width: 600px) {{
                    body, table, td, p, a, li, blockquote {{
                        -webkit-text-size-adjust: none !important;
                    }}
                    table {{
                        width: 100% !important;
                    }}
                    .responsive-image img {{
                        height: auto !important;
                        max-width: 100% !important;
                        width: 100% !important;
                    }}
                }}
            </style>
        </head>
        <body>
            <span class="preheader" style="display: none !important;">{variant.pre_header}</span>
            <table width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; margin: 0 auto;">
                <tr>
                    <td align="center" style="padding: 20px 0; background-color: #000000;">
                        <img src="https://example.com/samsung-logo.png" alt="Samsung" style="max-width: 150px;">
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px;">
                        <h1 style="color: #0056b3; font-size: 28px; margin-bottom: 20px;">{variant.subject_line}</h1>
                        <p style="font-size: 18px; line-height: 1.6; color: #666; margin-bottom: 30px;">{variant.pre_header}</p>

                        {body_html}

                    </td>
                </tr>
                <tr>
                    <td style="background-color: #f4f4f4; padding: 20px; text-align: center;">
                        <p style="font-size: 14px; color: #666; margin-bottom: 10px;">
                            Follow us on:
                            <a href="#" style="color: #0056b3; text-decoration: none;">Facebook</a> |
                            <a href="#" style="color: #0056b3; text-decoration: none;">Twitter</a> |
                            <a href="#" style="color: #0056b3; text-decoration: none;">Instagram</a> |
                            <a href="#" style="color: #0056b3; text-decoration: none;">YouTube</a>
                        </p>
                        <p style="font-size: 14px; color: #666; margin-bottom: 10px;">
                            This email has been sent to members who have requested to join the mailing list.
                            If you do not wish to receive emails, you can <a href="#" style="color: #0056b3; text-decoration: underline;">unsubscribe</a>.
                        </p>
                        <p style="font-size: 14px; color: #666; margin-bottom: 0;">
                            © 2024 Samsung Electronics Co. Ltd. All rights reserved.
                        </p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        state['html_email'] = html_template
        state['current_body'] = None

    except Exception as e:
        print(f"Error in HTML agent: {str(e)}")
        raise

    return state


async def add_approved_variant(state: EmailCampaignState):
    if 'variants' not in state:
        state['variants'] = []

    if state['current_variant']:
        approved_variant = {
            "tone": state['current_tone'],
            "content": state['current_variant'],
            "html_email": state['html_email']
        }

        state['variants'].append(approved_variant)

    next_tone_index = len(state.get('variants', [])) % len(TONES)
    state['current_tone'] = TONES[next_tone_index]

    state['current_variant'] = None
    state['qa_feedback'] = None
    state['html_email'] = None

    return state
