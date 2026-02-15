# AI Studio Handoff

This folder contains everything needed to generate the IronMind frontend using Google AI Studio.

## Files

1.  **`openapi.json`**: The full API specification (including local servers and debug security schemes).
2.  **`AI_STUDIO_PROMPT.md`**: The system prompt containing architecture rules, auth patterns, and tech stack details.
3.  **`DEV_AUTH.md`**: Documentation for the local `X-Debug-Uid` authentication strategy.

## Instructions

1.  Upload **all three files** to Google AI Studio.
2.  Paste the following instruction:
    > "Use the uploaded OpenAPI spec and AI_STUDIO_PROMPT.md to implement the full frontend. Follow the prompt strictly."
3.  The generated code will work with your local backend at `http://localhost:8080`.
