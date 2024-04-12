import os
import streamlit as st
import vertexai

from openai import OpenAI
from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    HarmBlockThreshold,
    HarmCategory,
    Part
)

PROJECT_ID = os.environ.get("GCP_PROJECT")  # Your Google Cloud Project ID
LOCATION = os.environ.get("GCP_REGION")  # Your Google Cloud Project Region
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") # OpenAI API key

vertexai.init(project=PROJECT_ID, location=LOCATION)

def generate_image(prompt: str) -> str:
    """OpenAI DALL-E 3 image generation."""
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    response = openai_client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    return image_url

def generate_text(
    model: GenerativeModel,
    prompt: str,
    stream: bool = True) -> str:
    """Google Cloud Gemini text model generation."""

    generation_config = {
        "temperature": 0.8,
        "max_output_tokens": 2048,
    }

    # Documentation: https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/configure-safety-attributes#safety_settings
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }

    responses = model.generate_content(
        prompt,
        generation_config=generation_config,
        safety_settings=safety_settings,
        stream=stream,
    )

    final_response = []
    for response in responses:
        try:
            final_response.append(response.text)
        except IndexError:
            final_response.append("")
            continue
    return " ".join(final_response)

def display_webpage() -> None:
    # Story elements dictionary
    story_dict = {}

    # Import local CSS style file
    with open('style.css') as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

    # Display webpage
    st.image("storybook.webp", width=350)
    st.header("Kids AI Story Creator", divider="rainbow")

    st.subheader("Character 1")
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        story_dict['character1_name'] = st.text_input(
            "Name",
            value="Ada",
            key="character1_name",
        )
    with col2:
        story_dict['character1_age'] = st.number_input(
            "Age",
            min_value=1,
            max_value=100,
            value=7,
            step=1,
            format="%d",
            key="character1_age")
    with col3:
        story_dict['character1_type'] = st.selectbox(
            "Character is a...",
            ('Human', 'Cat', 'Dog', 'Guinea Pig'),
            key='character1_type'
        )

    st.subheader("Character 2")
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        story_dict['character2_name'] = st.text_input(
            "Name",
            value="Nina",
            key="character2_name"
        )
    with col2:
        story_dict['character2_age'] = st.number_input(
            "Age",
            min_value=1,
            max_value=100,
            value=5,
            step=1,
            format="%d",
            key="character2_age")
    with col3:
        story_dict['character2_type'] = st.selectbox(
            "Character is a...",
            ('Human', 'Cat', 'Dog', 'Guinea Pig'),
            key='character2_type'
        )

    st.subheader("Story Elements")
    story_dict['story_location'] = st.selectbox(
        'Where does the story take place?',
        ('School', 'Home', 'The Ocean', 'Outer Space'),
        key='story_location',
    )
    story_dict['story_type'] = st.selectbox(
        'Where type of story is it?',
        ('Adventure', 'Comedy', 'Mystery', 'Sci-Fi'),
        key='story_type',
    )

    st.header("", divider="rainbow")
    generate_button = st.button(
        label="Generate my story",
        key="generate_t2t",
        type="primary",
    )
    if generate_button:
        generate_story(story_dict)

def generate_story(story_dict: dict) -> None:
    """Trigged when generate story button is clicked."""
    story_prompt = f"""
        Write a short story appropriate with words easy for a 2nd grader to read and based on the following premise: \n
        character1_name: {story_dict['character1_name']} \n
        character1_age: {story_dict['character1_age']} \n
        character1_type: {story_dict['character1_type']} \n

        character2_name: {story_dict['character2_name']} \n
        character2_age: {story_dict['character2_age']} \n
        character2_type: {story_dict['character2_type']} \n

        story_location: {story_dict['story_location']} \n
        story_type: {story_dict['story_type']} \n

        Target writing about 5 paragraphs for the story.
    """

    story_text = None
    image_prompt = None
    text_generation_model = GenerativeModel("gemini-1.0-pro")

    with st.spinner("Generating your story ..."):
        # Generate story text
        story_text = generate_text(
            text_generation_model,
            story_prompt
        )
        if story_text:
            st.write(story_text)
    with st.spinner("Generating image ..."):
        if story_text:
            # Generate image generation prompt
            prompt = f"""
                Generate an image generation prompt for this story:
                {story_text}
            """
            image_prompt = generate_text(
                text_generation_model,
                prompt
            )
            print(f"Image prompt: {image_prompt}")

            if image_prompt:
                # Generate image
                image_url = generate_image(image_prompt)
                if image_url:
                    st.image(image=image_url)

display_webpage()