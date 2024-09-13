import json
import asyncio
import html
from models import CampaignInput, Product
from tenacity import retry, wait_fixed, stop_after_attempt
from models import CampaignInput, Product

PRODUCT_CATEGORIES = {
    "tablets": {
        "options": ["Tab_A9", "Tab_S9_FE", "Tab_S9"],
    },
    "phones": {
        "options": ["Galaxy_S24", "Galaxy_Z_Flip_6", "Galaxy_Z_Fold_6"],
    },
    "watches": {
        "options": ["Watch_FE", "Watch_Ultra", "Watch6", "Watch7"],
    },
    "tv": {
        "options": ["Samsung_8K_TV", "Crystal_UHD_TV","OLED_TV"],
    }
}


GALAXY_AI_URL = "https://www.samsung.com/us/galaxy-ai/"

def retry_with_backoff(max_retries=3, wait_seconds=2):
    return retry(
        stop=stop_after_attempt(max_retries),
        wait=wait_fixed(wait_seconds),
        reraise=True
    )

def generate_html_body(body_content):
    body_dict = json.loads(body_content)
    html = ""

    for module in body_dict["product_modules"]:
        html += f"""
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-bottom: 20px;">
            <tr>
                <td style="padding: 20px; background-color: #f4f4f4; border-radius: 10px;">
                    <table width="100%" border="0" cellspacing="0" cellpadding="0">
                        <tr>
                            <td>
                                <h2 style="color: #0056b3; font-size: 24px; margin: 0 0 15px 0;">{module['title']}</h2>
                                <p style="font-size: 16px; line-height: 1.6; color: #333; margin-bottom: 20px;">{module.get('content','')}</p>
                                {'<a href="' + module.get('cta_link','') + '" style="display: inline-block; background-color: #0056b3; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold;">' + module['cta_text'] + '</a>' if module['cta_text'] else ''}
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        """

    html += f"""
    <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-top: 30px;">
        <tr>
            <td align="center">
                <a href="{body_dict['main_cta_link']}" style="display: inline-block; background-color: #0056b3; color: #ffffff; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-size: 18px; font-weight: bold;">{body_dict['main_cta']}</a>
            </td>
        </tr>
    </table>
    """

    return html

def get_user_input() -> CampaignInput:
    segment_name = input("Enter the segment name: ")
    campaign_type = input("Enter the campaign type: ")
    num_variants = int(input("Enter the number of variants needed per tone: "))
    num_products = int(input("Enter the number of products to include in the campaign: "))

    products = []
    for i in range(num_products):
        print(f"\nProduct {i+1}:")
        print("Available Product Categories:")
        for j, category in enumerate(PRODUCT_CATEGORIES.keys(), 1):
            print(f"{j}. {category.capitalize()}")

        category_choice = int(input("Select a product category (enter the number): ")) - 1
        category = list(PRODUCT_CATEGORIES.keys())[category_choice]

        print(f"\nAvailable {category} options:")
        options = PRODUCT_CATEGORIES[category]['options']
        for j, option in enumerate(options, 1):
            print(f"{j}. {option}")

        product_choice = int(input("Select a product (enter the number): ")) - 1
        product_name = options[product_choice]

        product = Product(
            name=product_name,
            category=category
        )
        products.append(product)

    return CampaignInput(
        segment_name=segment_name,
        campaign_type=campaign_type,
        products=products,
        num_variants=num_variants
    )