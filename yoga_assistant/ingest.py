"""
Data ingestion module for Yoga Assistant system.

This module handles loading and validating yoga data from CSV files.
"""

import pandas as pd
from typing import Dict


def load_yoga_data(csv_path: str) -> Dict[int, Dict]:
    """
    Load yoga data from CSV file and return as dictionary.

    Args:
        csv_path: Path to the yoga data CSV file

    Returns:
        Dictionary mapping pose IDs to pose data dictionaries

    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If CSV is missing required columns
    """
    # Required columns for the yoga dataset
    required_columns = [
        "id",
        "pose_name",
        "sanskrit_name",
        "category",
        "difficulty_level",
        "benefits",
        "contraindications",
        "breathing_pattern",
        "duration_or_reps",
        "modifications",
        "instructions",
    ]

    try:
        # Load CSV file
        df = pd.read_csv(csv_path)

        # Validate required columns exist
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(
                f"CSV missing required columns: {missing_columns}"
            )

        # Convert to dictionary mapping ID to pose data
        pose_dict = {
            row["id"]: row.to_dict() for _, row in df.iterrows()
        }

        print(f"✓ Loaded {len(pose_dict)} yoga poses from {csv_path}")

        return pose_dict

    except FileNotFoundError:
        raise FileNotFoundError(
            f"Yoga data file not found: {csv_path}"
        )
    except Exception as e:
        raise ValueError(f"Error loading yoga data: {str(e)}")


def validate_pose_data(pose_dict: Dict[int, Dict]) -> bool:
    """
    Validate that pose data has required structure and content.

    Args:
        pose_dict: Dictionary of pose data

    Returns:
        True if validation passes

    Raises:
        ValueError: If validation fails
    """
    if not pose_dict:
        raise ValueError("Pose dictionary is empty")

    # Check that all poses have required fields
    required_fields = [
        "id",
        "pose_name",
        "sanskrit_name",
        "category",
        "difficulty_level",
        "benefits",
        "contraindications",
        "instructions",
    ]

    for pose_id, pose in pose_dict.items():
        missing_fields = set(required_fields) - set(pose.keys())
        if missing_fields:
            raise ValueError(
                f"Pose {pose_id} missing fields: {missing_fields}"
            )

        # Validate that key fields are not empty
        if not pose.get("pose_name"):
            raise ValueError(
                f"Pose {pose_id} has empty pose_name"
            )

    print(f"✓ Validated {len(pose_dict)} poses")
    return True
