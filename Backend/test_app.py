import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("=== STARTING END-TO-END ENDPOINT TESTS ===")
    
    # 1. Signup
    print("\n1. Testing Signup...")
    signup_payload = {
        "username": f"test_student_{int(time.time())}",
        "password": "password123"
    }
    signup_resp = requests.post(f"{BASE_URL}/api/auth/signup", json=signup_payload)
    if signup_resp.status_code == 201:
        print("[OK] Signup successful:", signup_resp.json())
    else:
        print("[FAIL] Signup failed:", signup_resp.status_code, signup_resp.text)
        return

    # 2. Login
    print("\n2. Testing Login...")
    login_data = {
        "username": signup_payload["username"],
        "password": signup_payload["password"]
    }
    login_resp = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
    if login_resp.status_code == 200:
        token_info = login_resp.json()
        print("[OK] Login successful, got token")
        token = token_info["access_token"]
    else:
        print("[FAIL] Login failed:", login_resp.status_code, login_resp.text)
        return

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # 3. Get Current User Profile
    print("\n3. Testing Get Current User Profile...")
    me_resp = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    if me_resp.status_code == 200:
        print("[OK] Me endpoint successful:", me_resp.json())
    else:
        print("[FAIL] Me endpoint failed:", me_resp.status_code, me_resp.text)
        return

    # 4. Get Default Tags
    print("\n4. Testing List Tags...")
    tags_resp = requests.get(f"{BASE_URL}/api/tags", headers=headers)
    if tags_resp.status_code == 200:
        tags = tags_resp.json()
        print(f"[OK] List tags successful. Found {len(tags)} tags:")
        for t in tags[:3]:
            print(f"  - {t['name']}: {t['description']}")
    else:
        print("[FAIL] List tags failed:", tags_resp.status_code, tags_resp.text)
        return

    # 5. Add Custom Tag
    print("\n5. Testing Create Custom Tag...")
    custom_tag_payload = {
        "name": "Machine Learning",
        "description": "Artificial intelligence algorithms, regression, neural networks, and model training."
    }
    tag_resp = requests.post(f"{BASE_URL}/api/tags", json=custom_tag_payload, headers=headers)
    if tag_resp.status_code == 201:
        print("[OK] Custom tag created successfully:", tag_resp.json())
    elif tag_resp.status_code == 400 and "already exists" in tag_resp.text:
        print("[OK] Custom tag already exists (expected if re-run):", tag_resp.text)
    else:
        print("[FAIL] Custom tag creation failed:", tag_resp.status_code, tag_resp.text)
        return

    # 6. Analyze a Math Question
    print("\n6. Testing Question Analysis (Math)...")
    math_q_payload = {
        "text": "What is the derivative of x^3 + 4x^2 - 10?"
    }
    analyze_resp = requests.post(f"{BASE_URL}/api/questions/analyze", json=math_q_payload, headers=headers)
    if analyze_resp.status_code == 200:
        analysis = analyze_resp.json()
        print("[OK] Question analysis successful. Suggested tags:")
        for st in analysis["suggested_tags"][:3]:
            print(f"  - {st['name']}: Match score {st['similarity_score']:.4f}")
        # The top match should be Mathematics
        top_tag = analysis["suggested_tags"][0]["name"]
        print(f"  Top recommended tag is: '{top_tag}'")
    else:
        print("[FAIL] Question analysis failed:", analyze_resp.status_code, analyze_resp.text)
        return

    # 7. Add Question (with auto-tagging)
    print("\n7. Testing Submit Question (Math)...")
    submit_resp = requests.post(f"{BASE_URL}/api/questions", json=math_q_payload, headers=headers)
    if submit_resp.status_code == 201:
        q_data = submit_resp.json()
        print("[OK] Question created successfully. Assigned tags:")
        for t in q_data["tags"]:
            print(f"  - {t['name']}")
    else:
        print("[FAIL] Submit question failed:", submit_resp.status_code, submit_resp.text)
        return

    # 8. Add Question (with custom tag auto-tagging check)
    print("\n8. Testing Submit Question (ML)...")
    ml_q_payload = {
        "text": "Can you explain how backpropagation updates weights in a deep neural network?"
    }
    submit_ml_resp = requests.post(f"{BASE_URL}/api/questions", json=ml_q_payload, headers=headers)
    if submit_ml_resp.status_code == 201:
        q_ml_data = submit_ml_resp.json()
        print("[OK] Question created successfully. Assigned tags:")
        for t in q_ml_data["tags"]:
            print(f"  - {t['name']}")
    else:
        print("[FAIL] Submit question failed:", submit_ml_resp.status_code, submit_ml_resp.text)
        return

    # 9. Semantic Similarity Search
    print("\n9. Testing Semantic Similarity Search...")
    # Search for something semantically similar to the ML question, but with different words
    search_query = "training deep learning networks weights update mechanism"
    search_resp = requests.get(
        f"{BASE_URL}/api/questions/search",
        params={"query": search_query, "threshold": 0.3},
        headers=headers
    )
    if search_resp.status_code == 200:
        results = search_resp.json()
        print(f"[OK] Semantic search successful. Found {len(results)} matches:")
        for r in results:
            print(f"  - Match: '{r['text']}' (Similarity: {r['similarity_score']:.4f})")
    else:
        print("[FAIL] Semantic search failed:", search_resp.status_code, search_resp.text)
        return

    print("\n=== ALL TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()
