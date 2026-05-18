# Reviewify: An AI-Powered Automated Reviewer Generation System

## Overview
Reviewify is a Python-based educational productivity and automation system designed to help students automatically generate organized reviewer documents from lecture materials such as PowerPoint presentations and PDF lecture slides.

The system allows users to upload multiple PPT, PPTX, or PDF files. Reviewify automatically extracts lecture content, identifies important topics and headings, summarizes lengthy discussions, and reformats the extracted information into a clean two-column reviewer format commonly used by students for studying and printing.

The generated reviewer can be exported as:
- PDF (print-ready reviewer)
- DOCX (editable reviewer document)

The main objective of the system is to reduce the time and effort students spend manually compiling notes and creating reviewers for their courses.

---

# Main Features

## File Upload
- Upload multiple PPT, PPTX, and PDF lecture files
- Drag-and-drop upload interface
- Upload progress tracking
- File validation and size checking

## Lecture Content Extraction
- Extract slide titles
- Extract bullet points
- Extract paragraphs and lecture text
- Preserve topic hierarchy when possible

## AI Summarization
- Summarize long lecture content
- Condense overloaded slides
- Simplify reviewer notes while preserving key concepts

## Smart Topic Organization
- Detect chapter titles
- Detect lessons and sections
- Group related topics together
- Arrange reviewer flow logically

## Reviewer Generator
Generate:
- Two-column reviewer layout
- Compact print-friendly formatting
- Readable typography and spacing
- Organized headings and subtopics

## Export Features
Allow exporting generated reviewers into:
- PDF
- DOCX

## Reviewer Customization
Users can:
- choose concise or detailed reviewer mode
- adjust font size
- choose layout spacing
- enable or disable summaries

## Dashboard
Display:
- uploaded lecture materials
- generated reviewers
- recent files
- total processed documents

---

# Technologies

## Backend
- Python
- Flask
- SQLite

## File Processing
- python-pptx
- PyMuPDF or pdfplumber

## AI/NLP
- transformers
- summarization models

## Document Generation
- python-docx
- reportlab

## Frontend
- HTML
- TailwindCSS
- Vanilla JavaScript

---

# System Goal
The system should function as a real-world AI-powered study assistant capable of automatically generating clean, organized, editable, and printable reviewer documents from uploaded lecture slides and academic materials.

---

# Target Users
- College students
- Senior high school students
- Academic organizations
- Review centers
- Study groups

