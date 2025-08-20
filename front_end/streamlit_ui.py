# app.py
import streamlit as st
import requests 
import pandas as pd 
import plotly.graph_objects as go


def render_results(data:dict,key_prefix:str):
    """ Use render api responses across tabs"""
    try:
        metrics = data.get("dish_metrics",{}).get("metrics",{})
        if not metrics:
            st.error(f"Invalid Input Given input is not a Dish name or has Dish/Food")
            return 
        # Serving slider
        servings = st.slider(
            "How many servings?",
            1,
            25,
            1,
            key=f"{key_prefix}_slider"
        )
        if servings:
            total_carbon = metrics["carbon_per_serving_kg"] * servings

        # --- Overview Section
        st.subheader(f"{metrics['dish']} 🍕")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Carbon Footprint", f"{total_carbon:.2f} kg CO2e")
        col2.metric("Serving Size", f"{metrics['serving_size_g']:.2f} g")
        col3.metric("Estimation Accuracy", f"{metrics['estimation_accuracy']} %")

        st.markdown("### Additional Data")
        st.write(f"- Impact Rating (A–E): **{metrics['impact_rating']}**")
        st.write(f"- Carbon Footprint per Serving ≈ **{metrics['carbon_per_serving_kg']} kg CO2e**")
        st.write(f"- Average Serving Size ≈ **{metrics['serving_size_g']} g**")
        st.write(f"- Total Ingredients Count = **{metrics['ingredient_count']}**")

        st.info(
            f"🚗 The estimated carbon emissions of this meal are equivalent to driving "
            f"**{metrics['car_miles_equivalent']:.1f} miles** in a petrol car!"
        )

        # --- Ingredients Table
        st.markdown("## Ingredients")
        st.caption(
            f"Generated ingredients and estimated weights as per {servings} servings of {metrics['dish']}."
        )

        ingredients = data["dish_metrics"]["ingredients"]["ingredients"]
        lca_results = data["dish_metrics"]["lca"]["results"]

        lca_map = {item["ingredient_name"]: item for item in lca_results}
        merged_data = []
        for ing in ingredients:
            lca = lca_map.get(ing["ingredient_name"], {})
            merged_data.append({
                "Ingredient Name": ing["ingredient_name"].title(),
                "Ingredient Weight (kg)": ing["ingredient_weight_kg"] * servings,
                "Carbon Footprint (kg CO2e)": lca.get("carbon_footprint_kg_co2e"),
                "Matched?": lca.get("matched"),
                "Matched Ingredient": lca.get("matched_ingredient"),
                "Match Confidence": lca.get("match_confidence"),
                "LCA Source": lca.get("lca_source"),
            })
        df = pd.DataFrame(merged_data)
        st.dataframe(df, use_container_width=True)

        # --- Graph section (stacked bar)
        df_lca = pd.DataFrame(lca_results).rename(
        columns={
            "ingredient_name": "Ingredient",
            "farming_footprint_kg_co2e": "Farming (kg CO2e)",
            "packaging_footprint_kg_co2e": "Packaging (kg CO2e)",
            "processing_footprint_kg_co2e": "Processing (kg CO2e)",
            "retail_footprint_kg_co2e": "Retail (kg CO2e)",
            "transportation_footprint_kg_co2e": "Transportation (kg CO2e)"
        }
        )
        df_lca["Consumption (kg CO2e)"] = 0  # optional baseline

        stages = [
            "Consumption (kg CO2e)",
            "Farming (kg CO2e)",
            "Packaging (kg CO2e)",
            "Processing (kg CO2e)",
            "Retail (kg CO2e)",
            "Transportation (kg CO2e)",
        ]

        colors = {
            "Consumption (kg CO2e)": "#1f77b4",
            "Farming (kg CO2e)": "#ff7f0e",
            "Packaging (kg CO2e)": "#2ca02c",
            "Processing (kg CO2e)": "#d62728",
            "Retail (kg CO2e)": "#9467bd",
            "Transportation (kg CO2e)": "#17becf",
        }

        fig = go.Figure()

        for stage in stages:
            fig.add_trace(
                go.Scatter(
                    x=df_lca["Ingredient"],
                    y=df_lca[stage],
                    mode="lines",
                    stackgroup="one",  # enables stacking
                    name=stage,
                    line=dict(width=0.5),
                    fill="tonexty",
                    marker=dict(color=colors[stage])
                )
            )

        fig.update_layout(
            title="Life Cycle Assessment Breakdown (Stacked Area)",
            xaxis_title="Ingredient Name",
            yaxis_title="kg CO2e",
            template="plotly_dark",
            legend_title="Life Cycle Stage",
            height=500
        )

        st.subheader("Life Cycle Assessment Breakdown (Stacked Area)")
        st.caption("The following stacked area chart shows cumulative emissions per ingredient across all life cycle stages.")
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("🚜 Farming: 0.89 kg CO2e", expanded=False): 
            st.write( "The farm stage represents the environmental impact of the agricultural " "production of the raw ingredients, which includes any impact that is a " "result of farming methods and activities, whether that’s pesticide usage, " "use of machinery, or the land and water usage." ) 
        with st.expander("🏭 Processing: 0.07 kg CO2e", expanded=False): 
            st.write( "The processing stage represents the stage at which a product is made. " "For example, it could include the cleaning of raw products like fruit and veg, " "or it could include the combining of raw ingredients to make a ready meal. " "This stage usually happens inside factory walls." ) 
        with st.expander("📦 Packaging: 0.03 kg CO2e", expanded=False): 
            st.write( "The packaging stage refers to the type and quantity of packaging used for the product. " "The impact on the world can vary depending on material e.g. aluminium cans compared " "to glass bottles." ) 
        with st.expander("🚛 Transportation: 0.03 kg CO2e", expanded=False): 
            st.write( "The transport stage refers to the distribution of the product between supplier and retailer. " "The impact will vary depending on origin and destination of product, " "as well as the mode of transport." ) 
        with st.expander("🏬 Retail: 0.02 kg CO2e", expanded=False): 
            st.write( "The retail stage represents emissions arising from retail operations. " "This includes the impacts of any chilling at retail, and apportioned impacts " "of the retail facility, such as lighting and air conditioning." ) 
        with st.expander("🍽 Consumption: 0.00 kg CO2e", expanded=False): 
            st.write( "The Consumption stage represents the emissions arising from food preparation, " "such as appliance usage." )
    except Exception as e:
            st.error(f"Error fetching results: {e}")

    
# ---------- Page setup
st.set_page_config(
    page_title="Carbon Footprint Estimator",
    page_icon="🍃",
    layout="wide",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "Estimate the carbon score of any dish (Search or Vision)."
    },
)

# ---------- Minimal, elegant styling (works with both light/dark themes)
st.markdown(
    """
    <style>
      /* page background */
      .stApp {
        background: radial-gradient(1200px 600px at 15% -10%, rgba(93,93,255,0.06), rgba(0,0,0,0)) ,
                    radial-gradient(1200px 600px at 85% 110%, rgba(0,200,180,0.06), rgba(0,0,0,0));
      }

      /* glass card */
      .glass {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.12);
        box-shadow: 0 8px 40px rgba(0,0,0,0.15);
        backdrop-filter: blur(8px);
        border-radius: 16px;
        padding: 20px 22px;
      }

      /* headline */
      .hero h1 {
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem;
      }
      .hero p {
        opacity: 0.8;
        margin-top: 0;
      }

      /* nicer inputs (within cards) */
      .glass [data-testid="stTextInput"] input {
        border-radius: 12px;
        height: 3rem;
        padding: 0 1rem;
      }
      .glass [data-testid="stFileUploader"] section {
        border-radius: 12px !important;
      }
      .muted {opacity: .75}
      .chip {
        display:inline-block;padding:.35rem .6rem;border-radius:999px;
        border:1px solid rgba(255,255,255,.2); margin-right:.35rem; font-size:.85rem; opacity:.85
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Header / Hero
st.markdown(
    """
    <div class="hero">
      <h1>Carbon Footprint Estimator</h1>
      <p class="muted">Search by dish name or use vision to analyze an image.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- Tabs
tab_search, tab_vision = st.tabs(["🔎 Search", "🖼️ Vision"])

with tab_search:
    # --- Suggestions first
    st.caption("Try:")
    st.write(
        '<span class="chip">pizza</span><span class="chip">chicken biryani</span><span class="chip">paneer tikka</span>',
        unsafe_allow_html=True,
    )

    # --- Search form
    with st.form("search_form", clear_on_submit=False):
        dish_query = st.text_input(
            "Enter a dish to learn about its environmental impact",
            placeholder="e.g., chicken biryani, pizza, caesar salad",
        )
        submitted_search = st.form_submit_button("Search")

    # --- Image uploader
    img = st.file_uploader(
        "Or simply upload an image of the dish",
        type=["jpeg", "jpg", "png"],
        help="Max ~5MB. JPEG/PNG recommended.",
    )
    submitted_img = img is not None
    
    # --- Results area (only appears after Search or Upload)
    if submitted_search and dish_query.strip():
        # Clear old image results if any
        st.session_state.pop("api_data", None)
        st.session_state.pop("api_mode", None)

        # Call text search API
        url = f"http://localhost:8000/api/v1/estimator/estimate?dish={dish_query.strip()}"
        response = requests.post(url)
        st.session_state["api_data"] = response.json()
        st.session_state["api_mode"] = "search"
        
    elif submitted_img:
        # Clear old search results if any
        st.session_state.pop("api_data", None)
        st.session_state.pop("api_mode", None)

        # Call image API
        url = "http://localhost:8000/api/v1/estimator/estimate/image"
        files = {"file": img.getvalue()}
        response = requests.post(url, files={"file": ("upload.png", img.getvalue(), "image/png")})
        st.session_state["api_data"] = response.json()
        st.session_state["api_mode"] = "image"
    
    if "api_data" in st.session_state:
        try:
            render_results(st.session_state["api_data"],key_prefix="search")
        except Exception as e:
            st.error(f"Error rendering results: {e}")

with tab_vision:
    st.subheader("Vision")
    st.caption("Analyze a photo of a dish to estimate its carbon footprint.")
    
     # Camera input widget
    picture = st.camera_input("📷 Capture a dish photo")

    if picture is not None:
        # Convert camera capture to API request
        try:
            url = "http://localhost:8000/api/v1/estimator/estimate/image"
            response = requests.post(
                url,
                files={"file": ("capture.png", picture.getvalue(), "image/png")},
            )
            if response.status_code == 200:
                data = response.json()
                st.session_state["api_data"] = data
                st.session_state["api_mode"] = "image"

                st.success("Image uploaded successfully and processed.")
            else:
                st.error(f"API error: {response.status_code}")
        except Exception as e:
            st.error(f"Error connecting to API: {e}")
    if "api_data" in st.session_state:
        try:
            render_results(st.session_state["api_data"],key_prefix="image/png")
        except Exception as e:
            st.error(f"Error rendering results: {e}")