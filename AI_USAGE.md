# AI usage statement

List every use of an AI assistant (ChatGPT, Claude, Copilot, Gemini, etc.) in this project. Every member must be able to explain all submitted code and figures.

| Date | Tool | Task (what you asked) | Where it is used (file/section) | What you verified and how |
|---|---|---|---|---|
| 2026-11-18|ChatGPT (GPT-6) |Troubleshoot the dataset download script for Google Colab, including replacing the __file__-based directory path with an explicit project path. |Dataset download script, data/raw/ directory setup |Checked the directory structure in Colab and confirmed that UNHCR, World Bank, and IDMC raw files were present in data/raw/. |
| 2026-11-18|ChatGPT (GPT-6) |Debug the data preparation script, including handling Colab command-line arguments, correcting file paths, and resolving Python indentation and syntax errors. |Data preparation script, main() function and file-loading section |Ran the preparation script in Colab. Confirmed that all six processed CSV files were generated. Checked the reported row and column counts in the output. |
| 2026-11-18|ChatGPT (GPT-6) |Explain and organize the data cleaning results, dataset dimensions, missing values, duplicate records, and dataset integration results. |Data documentation, Data Cards section |Compared the documentation figures with the actual Colab execution output, including 49,798 cleaned UNHCR rows, 1,953 population rows, 1,953 GDP rows, and 1,125 IDMC rows. |
| 2026-11-18|ChatGPT (GPT-6) |Help structure the documentation for all six processed datasets and suggest a GitHub Markdown layout with collapsible sections. |data/README.md, Data Cards section |Checked dataset names, dimensions, time coverage, and cleaning decisions against the generated CSV files and preparation output. Original source licenses were left for further verification. |
| 2026-11-18|ChatGPT (GPT-6) |Provide guidance on creating the visual/ folder and uploading visualization files to GitHub. |Repository directory structure, [visual/](visual/)|Checked the GitHub folder structure and the steps required to upload image files. |

