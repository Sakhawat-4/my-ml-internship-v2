import os
import glob
import re
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv
import pdfplumber

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class StudyCoachAgent:
    def __init__(self):
        self.repo_path = Path("./my-ml-internship-v2")
        self.model = genai.GenerativeModel('gemini-pro')
        
    def read_file_content(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return ""
    
    def read_pdf_content(self, pdf_path):
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text()
                return text
        except:
            return ""
    
    def search_repo(self, keyword):
        results = []
        extensions = ['*.md', '*.py', '*.txt', '*.ipynb', '*.pdf']
        for ext in extensions:
            for file_path in self.repo_path.rglob(ext):
                if file_path.is_file():
                    if ext == '*.pdf':
                        content = self.read_pdf_content(file_path)
                    else:
                        content = self.read_file_content(file_path)
                    if keyword.lower() in content.lower():
                        results.append({
                            'file': str(file_path.relative_to(self.repo_path)),
                            'snippet': content[:500]
                        })
        return results
    
    def answer_question(self, question):
        print(f"\n🤔 Question: {question}")
        print("📚 Searching repository...")
        
        keywords = re.findall(r'\b\w+\b', question.lower())
        relevant_keywords = [k for k in keywords if len(k) > 3]
        
        all_results = []
        for keyword in relevant_keywords[:3]:
            results = self.search_repo(keyword)
            all_results.extend(results)
        
        context_text = "Here is information from the user's internship repository:\n\n"
        if all_results:
            for result in all_results[:5]:
                context_text += f"File: {result['file']}\n"
                context_text += f"Content: {result['snippet'][:300]}...\n\n"
        else:
            context_text = "No relevant information found in the repository."
        
        prompt = f"""You are a helpful study coach for an ML engineering intern.
        Your job is to answer questions based ONLY on the provided repository content.
        
        User Question: {question}
        
        Repository Content:
        {context_text}
        
        Instructions:
        1. If the answer is in the content above, provide it clearly with the source file name.
        2. If the answer is NOT in the content, say "I couldn't find this in your repository."
        3. Don't make up information - only use what's provided.
        
        Your response:"""
        
        response = self.model.generate_content(prompt)
        return response.text

if __name__ == "__main__":
    coach = StudyCoachAgent()
    print("🎓 Welcome to your ML Study Coach Agent!\n")
    
    test_questions = [
        "What is the data dictionary?",
        "Show me the feature leakage notebook"
    ]
    
    for q in test_questions:
        print("\n" + "="*50)
        answer = coach.answer_question(q)
        print(f"\n💡 Answer:\n{answer}")