"""
Streamlit application for Yoga RAG Assistant.

This is the main entry point for the Yoga Assistant web interface.
It provides a simple UI for asking questions about yoga poses and
receiving context-aware answers powered by RAG.
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Import application modules
from ingest import load_yoga_data, validate_pose_data
from retrieval import create_retrieval_system
from rag import create_llm_client, rag_pipeline
from db import log_conversation, update_feedback

# Load environment variables
load_dotenv()


def initialize_app():
    """
    Initialize the application by loading data and creating indices.

    This runs once at startup and stores everything in session state.
    """
    if "initialized" not in st.session_state:
        with st.spinner("Loading yoga knowledge base..."):
            # Load yoga data
            data_path = os.getenv("DATA_PATH", "data/yoga_data.csv")
            pose_dict = load_yoga_data(data_path)
            validate_pose_data(pose_dict)

            # Create retrieval system
            retrieval_system = create_retrieval_system(pose_dict)

            # Create LLM client
            llm_client = create_llm_client()

            # Store in session state
            st.session_state.pose_dict = pose_dict
            st.session_state.retrieval_system = retrieval_system
            st.session_state.llm_client = llm_client
            st.session_state.initialized = True

            # Initialize conversation history
            st.session_state.conversation_history = []

        st.success("✓ Yoga Assistant ready!")


def main():
    """
    Main application function.
    """
    # Page configuration
    st.set_page_config(
        page_title="Yoga Assistant",
        page_icon="🧘",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Title and description
    st.title("🧘 Yoga Assistant")
    st.markdown(
        """
        Ask me anything about yoga poses, breathing techniques, and
        sequencing. I'll provide accurate, knowledge-grounded guidance
        based on a comprehensive yoga database.
        """
    )

    # Initialize application
    try:
        initialize_app()
    except Exception as e:
        st.error(f"Failed to initialize application: {str(e)}")
        st.info(
            "Check your .env file and ensure all required "
            "variables are set correctly."
        )
        st.stop()

    # Main interface
    st.markdown("---")

    # Question input
    question = st.text_input(
        "Ask your question:",
        placeholder="e.g., What are the benefits of Downward-Facing Dog?",
        key="question_input",
    )

    # Submit button
    if st.button("Get Answer", type="primary"):
        if question.strip():
            # Show loading state
            with st.spinner("Thinking..."):
                # Get model from environment or use default
                model = os.getenv("LLM_MODEL", "deepseek-ai/DeepSeek-V3")
                top_k = int(os.getenv("TOP_K_RETRIEVAL", "5"))

                # Run RAG pipeline
                result = rag_pipeline(
                    question=question,
                    retrieval_system=st.session_state.retrieval_system,
                    pose_dict=st.session_state.pose_dict,
                    client=st.session_state.llm_client,
                    model=model,
                    top_k=top_k,
                )

                # Log conversation to database
                try:
                    log_conversation(
                        question=question,
                        answer=result["answer"],
                        model=result["model"],
                        retrieved_docs=result["retrieved_poses"],
                        response_time_ms=result["response_time_ms"],
                        tokens_used=result["tokens_used"],
                        conversation_id=result["conversation_id"],
                    )
                except Exception as e:
                    st.warning(f"Note: Logging failed ({str(e)})")

                # Store in conversation history
                st.session_state.conversation_history.append(
                    {
                        "question": question,
                        "answer": result["answer"],
                        "conversation_id": result["conversation_id"],
                        "retrieved_poses": result["retrieved_poses"],
                        "response_time_ms": result["response_time_ms"],
                        "tokens_used": result["tokens_used"],
                    }
                )

                # Display current answer immediately
                st.markdown("---")
                st.markdown("**Answer:**")
                st.markdown(result["answer"])

                # Show metadata in expander
                with st.expander("Details"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            "Response Time", f"{result['response_time_ms']}ms"
                        )
                    with col2:
                        st.metric("Tokens Used", result["tokens_used"])

                    if result["retrieved_poses"]:
                        st.markdown("**Retrieved Poses:**")
                        for pose in result["retrieved_poses"]:
                            st.markdown(
                                f"- {pose['pose_name']} "
                                f"({pose['category']}, "
                                f"{pose['difficulty_level']})"
                            )

                # Feedback for current answer
                st.markdown("**Was this helpful?**")
                col1, col2 = st.columns([1, 1])

                with col1:
                    if st.button("👍 Yes", key="current_thumbs_up"):
                        success = update_feedback(result["conversation_id"], 1)
                        if success:
                            st.success("Thanks for your feedback!")
                        else:
                            st.error("Failed to save feedback")

                with col2:
                    if st.button("👎 No", key="current_thumbs_down"):
                        success = update_feedback(
                            result["conversation_id"], -1
                        )
                        if success:
                            st.success("Thanks for your feedback!")
                        else:
                            st.error("Failed to save feedback")
        else:
            st.warning("Please enter a question.")

    # Display past conversation history (excluding current)
    if len(st.session_state.conversation_history) > 1:
        st.markdown("---")

        # Exclude the most recent conversation (already shown above)
        past_convos = st.session_state.conversation_history[:-1]
        num_past = len(past_convos)

        with st.expander(
            f"📜 Past Conversations ({num_past})",
            expanded=False,
        ):
            # Show most recent first (reversed)
            for i, conv in enumerate(reversed(past_convos)):
                # Each conversation in its own expander
                question_preview = conv["question"][:80]
                if len(conv["question"]) > 80:
                    question_preview += "..."

                with st.expander(
                    f"Q: {question_preview}",
                    expanded=False,
                ):
                    # Answer
                    st.markdown("**Answer:**")
                    st.markdown(conv["answer"])

                    st.markdown("---")

                    # Metadata
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            "Response Time", f"{conv['response_time_ms']}ms"
                        )
                    with col2:
                        st.metric("Tokens Used", conv["tokens_used"])

                    # Retrieved poses
                    if conv["retrieved_poses"]:
                        st.markdown("**Retrieved Poses:**")
                        for pose in conv["retrieved_poses"]:
                            st.markdown(
                                f"- {pose['pose_name']} "
                                f"({pose['category']}, "
                                f"{pose['difficulty_level']})"
                            )

                    st.markdown("---")

                    # Feedback buttons
                    st.markdown("**Was this helpful?**")
                    col1, col2 = st.columns([1, 1])

                    with col1:
                        if st.button("👍 Yes", key=f"thumbs_up_{i}"):
                            success = update_feedback(
                                conv["conversation_id"], 1
                            )
                            if success:
                                st.success("Thanks for your feedback!")
                            else:
                                st.error("Failed to save feedback")

                    with col2:
                        if st.button("👎 No", key=f"thumbs_down_{i}"):
                            success = update_feedback(
                                conv["conversation_id"], -1
                            )
                            if success:
                                st.success("Thanks for your feedback!")
                            else:
                                st.error("Failed to save feedback")

    # Sidebar with information
    with st.sidebar:
        st.header("About")
        st.markdown(
            """
            This Yoga Assistant uses Retrieval-Augmented Generation
            (RAG) to provide accurate answers about yoga poses,
            breathing techniques, and sequencing.

            **Features:**
            - 🔍 Hybrid search (text + semantic)
            - 🤖 LLM-powered responses
            - 📊 Conversation logging
            - 👍👎 Feedback collection
            """
        )

        if st.session_state.get("initialized"):
            st.markdown("---")
            st.markdown(
                f"**Poses loaded:** " f"{len(st.session_state.pose_dict)}"
            )
            st.markdown(
                f"**Conversations:** "
                f"{len(st.session_state.conversation_history)}"
            )


if __name__ == "__main__":
    main()
