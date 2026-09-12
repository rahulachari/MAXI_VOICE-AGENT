"""
JARVIS AI Query Tool
Answers informational questions without executing desktop automation actions.
"""

import json
import re
import urllib.request
from .base import BaseTool, ToolResult
from jarvis.app.config import config


class AIQueryTool(BaseTool):
    name = "AIQueryTool"
    description = "Provides concise, spoken explanations for general knowledge questions."

    def execute(self, action: str, **kwargs) -> ToolResult:
        if action == "deep_explanation":
            return self._deep_explanation(kwargs.get("topic", ""))

        query = kwargs.get("query", "")
        precomputed = kwargs.get("answer")
        from jarvis.voice.text_to_speech import clean_spoken_text

        q_lower = (query or "").lower()

        # Check if precomputed answer is invalid, placeholder, or contaminated with few-shot examples
        is_placeholder = False
        if precomputed:
            p_lower = precomputed.lower()
            if any(phrase in p_lower for phrase in [
                "searching the web", "searching google", "looking that up", "pulling up",
                "fetching the", "initiating a web search", "executing a targeted web search",
                "checking today's", "let me search", "searching for", "retrieving", "i will search"
            ]):
                is_placeholder = True
            # Discard few-shot contamination (e.g. Radhe Shyam when query is about another movie)
            if "radhe" in p_lower and "radhe" not in q_lower:
                is_placeholder = True
            if any(term in q_lower for term in ["sql", "code", "coding", "python", "javascript", "salary", "query", "table"]):
                is_placeholder = True

        if precomputed and not is_placeholder:
            full_det = kwargs.get("full_details") or precomputed
            clean_text = clean_spoken_text(full_det)
            return ToolResult(status="SUCCESS", message=clean_text, data={"query": query, "answer": full_det, "full_details": full_det})

        if not query:
            return ToolResult(status="FAILED", message="No query provided.")

        gemini_key = config.get("gemini_api_key")
        groq_key = config.get("groq_api_key") or os.getenv("GROQ_API_KEY")

        if groq_key or gemini_key:
            from datetime import datetime
            now_str = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")

            is_coding = any(
                term in q_lower
                for term in ["sql", "code", "coding", "python", "javascript", "java", "c++", "c#", "html", "css", "query", "function", "algorithm", "join", "select", "table", "salary", "program", "script", "regex"]
            )

            is_cooking = not is_coding and (
                any(
                    term in q_lower
                    for term in [
                        "prepare", "cook", "recipe", "bake", "making", "biryani", "dish", "curry", "dum",
                        "ingredients", "tea", "coffee", "cocktail", "dosa", "roti", "pasta", "pizza",
                        "paneer", "chicken", "mutton", "fish", "soup", "salad", "cake", "sauce", "rice",
                        "gravy", "dal", "sambar", "halwa", "pulao", "kebab", "omelette", "egg", "fry", "boil"
                    ]
                ) and any(
                    term in q_lower
                    for term in ["how", "recipe", "steps", "prepare", "cook", "make", "guide", "procedure", "instructions", "method", "process"]
                )
                or q_lower.startswith(("how to prepare", "how to cook", "how to make", "steps to make", "steps to prepare", "steps to cook", "recipe for"))
                or q_lower.endswith((" recipe", " preparation"))
            )

            is_puzzle = any(
                term in q_lower
                for term in ["riddle", "puzzle", "brain teaser", "what am i", "who am i", "solve this", "conundrum"]
            )

            # Check if query needs real-time web context (e.g. today's match, live scores, IMDb ratings, movies)
            needs_live_ctx = not is_coding and not is_cooking and not is_puzzle and (
                is_placeholder or any(
                    term in q_lower
                    for term in ["today", "match", "score", "schedule", "cricket", "current", "latest", "now", "live", "vs", "rating", "imdb", "mbd", "movie", "release", "box office", "who won"]
                )
            )
            live_ctx = self._search_ddg_lite(query) if needs_live_ctx else ""

            prompt_text = query
            if live_ctx:
                prompt_text = f"Question: '{query}'\nLive Web Search Context:\n{live_ctx}"

            if is_coding:
                instruction = (
                    f"Current Date & Time: {now_str}\n"
                    "You are JARVIS, an elite AI developer and programming assistant. "
                    "Provide a crystal-clear, articulate explanation followed by the exact, correct code snippet or SQL query. "
                    "Format code cleanly with proper syntax and indentation. "
                    "Keep the explanation direct, practical, and immediately usable. Avoid unnecessary conversational fluff."
                )
                max_tokens = 550
            elif is_cooking:
                instruction = (
                    f"Current Date & Time: {now_str}\n"
                    "You are JARVIS, an expert master chef and culinary instructor. "
                    "The user is asking how to prepare or cook a food item or recipe. "
                    "STRICT FORMATTING RULE: NEVER output a continuous paragraph or single wall of text! "
                    "You MUST structure the instructions as clean, sequential, numbered steps from start to finish. "
                    "Each step MUST start with 'Step X: **[Short Title]** - [Clear, concise, specific instruction]'.\n"
                    "Example:\n"
                    "Step 1: **Marinate** - Mix chicken with yogurt, ginger-garlic paste, chili powder, and spices. Let rest for 1 hour.\n"
                    "Step 2: **Parboil Rice** - Boil soaked basmati rice with whole spices and salt until 70% cooked; drain well.\n"
                    "Step 3: **Layering** - Place marinated chicken at bottom of heavy pot, layer rice over it, and top with fried onions and saffron.\n"
                    "Step 4: **Dum Cooking** - Seal pot with foil or dough. Cook on high for 5 minutes, then lowest flame for 20 minutes.\n"
                    "Step 5: **Rest & Serve** - Let sit for 10 minutes, then fluff gently and serve hot with raita.\n"
                    "Provide 4 to 6 sequential steps. Keep instructions crystal clear and easy to follow."
                )
                max_tokens = 650
            elif is_puzzle:
                instruction = (
                    f"Current Date & Time: {now_str}\n"
                    "You are JARVIS, a master of logic, riddles, and puzzles. "
                    "Give a concise, clever answer directly revealing the solution followed by a 1-sentence witty explanation. "
                    "Be sharp, articulate, and completely spoiler-free of other solutions."
                )
                max_tokens = 150
            else:
                instruction = (
                    f"Current Date & Time: {now_str}\n"
                    "You are JARVIS, an omniscient personal AI companion and chat box agent like Google Gemini. "
                    "Give a direct, simple, and crystal-clear answer in 2 to 3 natural sentences (under 50 words total). "
                    "State the practical facts, movie ratings (e.g. IMDb), sports schedules, or answers directly for the specific entity asked. "
                    "ZERO placeholder comments like 'Searching the web...', ZERO conversational fluff, and ZERO disclaimers. "
                    "NEVER say 'I do not have access' or 'as an AI'. NEVER include URLs. "
                    "Write clean plain text to show on screen and read aloud."
                )
                max_tokens = 180

            raw_answer = None

            # 1. Try Groq first for blazing sub-400ms speed
            if groq_key:
                groq_models = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]
                groq_url = "https://api.groq.com/openai/v1/chat/completions"
                groq_headers = {
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0",
                }
                for g_mod in groq_models:
                    try:
                        g_payload = {
                            "model": g_mod,
                            "messages": [
                                {"role": "system", "content": instruction},
                                {"role": "user", "content": prompt_text},
                            ],
                            "max_tokens": max_tokens,
                            "temperature": 0.2,
                        }
                        req = urllib.request.Request(groq_url, data=json.dumps(g_payload).encode("utf-8"), headers=groq_headers)
                        with urllib.request.urlopen(req, timeout=5) as resp:
                            g_data = json.loads(resp.read().decode("utf-8"))
                        ans = g_data["choices"][0]["message"]["content"].strip()
                        if ans:
                            raw_answer = ans
                            break
                    except Exception as ge:
                        print(f"[AIQueryTool] Groq model {g_mod} failed: {ge}")
                        continue

            # 2. Fall back to Gemini if Groq failed or key unavailable
            if not raw_answer and gemini_key:
                models = [
                    "gemini-flash-lite-latest",
                    "gemini-3.5-flash",
                    "gemini-3.5-flash-lite",
                    "gemini-3.1-flash-lite",
                    "gemini-flash-latest",
                ]
                payload = {
                    "contents": [{"parts": [{"text": prompt_text}]}],
                    "systemInstruction": {"parts": [{"text": instruction}]},
                    "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.2},
                }
                data_bytes = json.dumps(payload).encode("utf-8")

                for model in models:
                    try:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
                        req = urllib.request.Request(
                            url,
                            data=data_bytes,
                            headers={"Content-Type": "application/json"},
                            method="POST",
                        )
                        with urllib.request.urlopen(req, timeout=8) as resp:
                            data = json.loads(resp.read().decode("utf-8"))
                        raw_answer = data["candidates"][0]["content"]["parts"][0]["text"]
                        if raw_answer:
                            break
                    except Exception as e:
                        err_str = str(e)
                        if "429" in err_str:
                            continue
                        print(f"[AIQueryTool] Gemini model {model} failed: {e}")

            if raw_answer:
                if is_coding:
                    parts = raw_answer.split("```")
                    summary_speech = parts[0].strip() if parts else raw_answer
                    clean_spoken = clean_spoken_text(summary_speech)
                    return ToolResult(
                        status="SUCCESS",
                        message=clean_spoken or "Here is the code solution.",
                        data={"query": query, "answer": raw_answer, "full_details": raw_answer},
                    )
                elif is_cooking:
                    step_ordinals = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth"]
                    raw_lines = [l.strip() for l in raw_answer.split("\n") if l.strip()]
                    spoken_steps = []
                    idx = 0
                    for line in raw_lines:
                        m = re.match(r'^(?:Step\s*\d+[:.]?|\d+[\).])\s*(?:\*\*)?([^*\n:-]+)?(?:\*\*)?\s*[-:]?\s*(.*)', line, re.IGNORECASE)
                        if m:
                            title = (m.group(1) or "").strip()
                            body = (m.group(2) or "").strip()
                            ordinal = step_ordinals[idx] if idx < len(step_ordinals) else f"Step {idx+1}"
                            idx += 1
                            if title and body:
                                spoken_steps.append(f"{ordinal}, {title}: {body}")
                            elif body:
                                spoken_steps.append(f"{ordinal}, {body}")
                            elif title:
                                spoken_steps.append(f"{ordinal}, {title}")

                    if spoken_steps:
                        spoken_text = "Here is how to prepare it step by step. " + " ".join(spoken_steps)
                    else:
                        spoken_text = raw_answer

                    clean_spoken = clean_spoken_text(spoken_text)
                    return ToolResult(
                        status="SUCCESS",
                        message=clean_spoken or "Here is the step-by-step preparation process.",
                        data={"query": query, "answer": raw_answer, "full_details": raw_answer},
                    )
                else:
                    clean_spoken = clean_spoken_text(raw_answer)
                    return ToolResult(
                        status="SUCCESS",
                        message=clean_spoken,
                        data={"query": query, "answer": raw_answer, "full_details": raw_answer},
                    )

            # If all cloud models rate-limited (429) or offline
            return ToolResult(
                status="SUCCESS",
                message=f"Regarding {query}, your cloud AI service is momentarily busy. Please try again in a few seconds.",
                data={"query": query, "error": "rate_limited"},
            )

        return ToolResult(status="SUCCESS", message=f"I heard your question about '{query}'. Please configure your AI API keys for reasoning.")


    def _search_ddg_lite(self, query: str) -> str:
        """Fetches instant live search snippets from DuckDuckGo lite for the exact query."""
        import urllib.request
        import urllib.parse
        import re
        try:
            # Clean search query: do not pollute movie/rating queries with current date unless sports/match
            q_term = query
            q_lower = query.lower()
            if any(term in q_lower for term in ["match", "today", "live score", "score"]):
                from datetime import datetime
                q_term = f"{query} {datetime.now().strftime('%B %d, %Y')}"

            data = urllib.parse.urlencode({'q': q_term}).encode('utf-8')
            req = urllib.request.Request(
                'https://lite.duckduckgo.com/lite/',
                data=data,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
            snippets = re.findall(r'class=[\'"]result-snippet[\'"][^>]*>(.*?)</td>', html, re.DOTALL)
            clean = [re.sub(r'<[^>]+>', '', s).strip() for s in snippets[:4]]
            return "\n".join(clean)
        except Exception:
            return ""

    def _deep_explanation(self, topic: str) -> ToolResult:
        import urllib.parse
        import urllib.request
        import re
        from jarvis.utils.text_cleaner import clean_spoken_text
        from jarvis.utils.cursor_logger import log_layer

        if not topic:
            return ToolResult(status="FAILED", message="I need a topic to explain.")

        gemini_key = config.get("gemini_api_key")
        if not gemini_key:
            return ToolResult(status="FAILED", message="API key is required for deep explanations.")

        # 1. Scrape DDG for live context
        search_context = ""
        try:
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(topic)}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                html = response.read().decode('utf-8')
            
            snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
            if snippets:
                clean_snippets = [re.sub(r'<[^>]+>', '', s).strip() for s in snippets[:3]]
                search_context = "\n".join(clean_snippets)
                log_layer(4, "Deep Explanation search context retrieved", lines=len(clean_snippets))
        except Exception as e:
            log_layer(2, "DDG Search failed for deep explanation", error=str(e))

        # 2. Query Gemini
        prompt = (
            f"The user wants a deep explanation for: '{topic}'.\n\n"
            f"Here is some live search context (if relevant):\n{search_context}\n\n"
            "Provide two things in a strictly formatted JSON response:\n"
            "1. 'spoken_summary': A crisp, 2-3 sentence summary designed to be spoken aloud. No markdown.\n"
            "2. 'long_explanation': A highly detailed, well-organized explanation using Markdown headers (##) and bullet points. "
            "Cover what it is, how it works, and context (like business model or interview prep if relevant). Make it rich and structured for reading."
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4, "responseMimeType": "application/json"},
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        
        models = [
            "gemini-flash-lite-latest",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3.6-flash",
            "gemini-flash-latest",
        ]
        last_error = None
        
        for model in models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
                req = urllib.request.Request(url, data=data_bytes, headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                
                answer_text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(answer_text)
                    
                spoken_summary = clean_spoken_text(parsed.get("spoken_summary", f"Here is an explanation of {topic}."))
                long_explanation = parsed.get("long_explanation", "")
                
                return ToolResult(
                    status="SUCCESS",
                    message=spoken_summary,
                    data={"full_details": long_explanation, "topic": topic}
                )
            except Exception as e:
                last_error = e
                if "429" in str(e):
                    continue
                print(f"[AIQueryTool] Deep explanation model {model} failed: {e}")
                
        return ToolResult(status="FAILED", message=f"Failed to generate deep explanation. AI API rate limited (429). Please wait a moment.")
