ESCALATION_TRIGGERS = [
    "talk to human", "speak to agent", "connect me", "real person", 
    "human support", "speak to someone", "escalate", "talk to someone", "agent please"
]

LEAD_TRIGGERS = [
    "contact me", "call me", "reach me", "get back to me", "interested in", 
    "schedule", "appointment", "demo", "quote", "pricing", "leave my details"
]

def handle_query(question: str, query_function) -> dict:
    """
    Decides how to handle different types of user queries before calling RAG.
    """
    question_lower = question.lower()
    
    # 1. Check for escalation
    for trigger in ESCALATION_TRIGGERS:
        if trigger in question_lower:
            return {
                "answer": (
                    "I'll connect you with our support team!\n"
                    "📞 Phone: [Magppie phone]\n"
                    "📧 Email: support@magppie.com\n\n"
                    "⏰ Available Mon–Sat 9am–6pm\n"
                    "Or fill in your details below for a callback!"
                ),
                "escalation": True,
                "lead_intent": False
            }
            
    # 2. Check for lead intent
    for trigger in LEAD_TRIGGERS:
        if trigger in question_lower:
            rag_answer = query_function(question)
            nudge = "\n\nWould you like me to arrange a callback or share more details? You can leave your contact info below."
            return {
                "answer": rag_answer + nudge,
                "escalation": False,
                "lead_intent": True
            }
            
    # 3. Normal Query
    rag_answer = query_function(question)
    return {
        "answer": rag_answer,
        "escalation": False,
        "lead_intent": False
    }

if __name__ == "__main__":
    import json
    import sys
    
    # Ensure stdout handles utf-8 characters properly on Windows
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    
    # Dummy RAG function to avoid API usage during logic tests
    def dummy_query_function(q):
        return f"[MOCK RAG ANSWER] Information about '{q}'."
        
    print("--- Testing Escalation Case ---")
    esc_response = handle_query("I am frustrated, let me speak to someone!", dummy_query_function)
    print(json.dumps(esc_response, indent=2, ensure_ascii=False))
    
    print("\n--- Testing Lead Intent Case ---")
    lead_response = handle_query("I'm interested in the pricing of the kitchen.", dummy_query_function)
    print(json.dumps(lead_response, indent=2, ensure_ascii=False))
    
    print("\n--- Testing Normal Query Case ---")
    normal_response = handle_query("Where is the store located?", dummy_query_function)
    print(json.dumps(normal_response, indent=2, ensure_ascii=False))
