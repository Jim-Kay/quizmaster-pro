#!/usr/bin/env python
import os
import sys
import json
from pathlib import Path
from datamodel_code_generator import InputFileType, generate
from datamodel_code_generator.model import DataModelType

# Add the parent directory to sys.path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from models.schemas import (
    Blueprint, 
    Topic, 
    TerminalObjective, 
    EnablingObjective, 
    Question,
    Assessment,
    CognitiveLevelEnum
)

def generate_schema_file(models, output_path: Path):
    """Generate a temporary JSON schema file from Pydantic models"""
    schema_dict = {
        "$defs": {}
    }
    
    # Add each model's schema to the definitions
    for model in models:
        schema = model.model_json_schema()
        # Remove the $defs from individual schemas to avoid duplication
        if "$defs" in schema:
            schema_dict["$defs"].update(schema["$defs"])
            del schema["$defs"]
        schema_dict["$defs"][model.__name__] = schema

    # Write the combined schema to a file
    temp_schema_file = output_path.parent / "temp_schema.json"
    with open(temp_schema_file, "w") as f:
        json.dump(schema_dict, f, indent=2)
    
    return temp_schema_file

def main():
    # Path to frontend types directory
    types_dir = Path(__file__).parent.parent.parent / "frontend" / "types"
    types_dir.mkdir(exist_ok=True)
    output_file = types_dir / "schemas.ts"
    
    # Models to generate types for
    models = [
        Blueprint,
        Topic,
        TerminalObjective,
        EnablingObjective,
        Question,
        Assessment,
        CognitiveLevelEnum
    ]
    
    # Generate temporary schema file
    schema_file = generate_schema_file(models, output_file)
    
    try:
        # Generate TypeScript types
        generate(
            str(schema_file),
            input_file_type=InputFileType.JsonSchema,
            output=str(output_file),
            target_python_version="3.11",
            output_model_type=DataModelType.TypeScript,
            use_title_as_name=True,
            use_schema_description=True,
            enum_field_as_literal=True,
            use_double_quotes=True,
            style={"typescript": {"quote-style": "double"}},
            field_constraints=True,
            snake_case_field=True,
            strict_nullable=True,
        )
        print(f"Generated TypeScript types at: {output_file}")
    finally:
        # Clean up temporary schema file
        if schema_file.exists():
            schema_file.unlink()

if __name__ == "__main__":
    main()
