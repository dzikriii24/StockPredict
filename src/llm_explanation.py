"""
llm_explanation.py — Converts structured financial data into beginner-friendly "Bahasa Bayi".

Uses Google Gemini API if GEMINI_API_KEY is available in the environment.
Falls back to a deterministic template if the API is unavailable.
"""

import os
import json
from typing import Dict, Any

# Ensure python-dotenv is loaded
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def _get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return None
        
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except ImportError:
        return None

def generate_explanation(data: Dict[str, Any]) -> str:
    """
    Generate a beginner-friendly explanation of the structured data.
    """
    client = _get_gemini_client()
    
    if client:
        try:
            return _generate_with_gemini(client, data)
        except Exception as e:
            print(f"⚠️ Gemini API failed: {e}. Using fallback.")
            return _generate_fallback(data)
    else:
        return _generate_fallback(data)

def _generate_with_gemini(client, data: Dict[str, Any]) -> str:
    prompt = f"""
    Kamu adalah asisten analisis saham untuk PEMULA (orang yang tidak mengerti trading sama sekali).
    Tugasmu adalah menjelaskan data terstruktur berikut menggunakan bahasa Indonesia yang sangat santai, kasual, dan gampang dipahami ("bahasa bayi").
    
    Data Saham:
    {json.dumps(data, indent=2)}
    
    Aturan MENGGUNAKAN BAHASA:
    - Gunakan bahasa yang natural, seakan-akan kamu sedang ngobrol dengan teman di warung kopi.
    - Jangan gunakan istilah keuangan yang rumit (hindari kata-kata seperti "overbought", "bearish crossover", "resistance").
    - Jika menjelaskan RSI: jelaskan sebagai "tenaga harga".
    - Jika menjelaskan MACD: jelaskan sebagai "arah kekuatan harga saat ini".
    - Jika menjelaskan Sentimen Berita: jelaskan apakah beritanya lagi ramai, positif, atau campur-campur.
    - Jika menjelaskan Prediksi ML: jelaskan bahwa "sistem pintar kita melihat ada peluang X, tapi ini cuma prediksi, bukan kepastian."
    
    Aturan PENTING (DISCLAIMER):
    - JANGAN PERNAH menyuruh user untuk beli atau jual.
    - JANGAN PERNAH bilang "pasti naik" atau "pasti turun".
    - Selalu sisipkan peringatan bahwa ini hanya analisis, bukan kepastian.
    
    Format Output yang Diharapkan (singkat saja, maksimal 2-3 paragraf):
    "Singkatnya: ..."
    (Lalu jelaskan poin-poinnya secara mengalir)
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "temperature": 0.7,
            "max_output_tokens": 300,
        }
    )
    return response.text.strip()

def _generate_fallback(data: Dict[str, Any]) -> str:
    """Fallback deterministic text generator when LLM is unavailable."""
    ticker = data.get("ticker", "Saham ini")
    rsi = data.get("rsi", 50)
    macd = data.get("macd", "neutral")
    prediction = data.get("prediction_1d", "HOLD")
    pred_5d = data.get("prediction_5d", "UNKNOWN")
    pred_20d = data.get("prediction_20d", "UNKNOWN")
    impact = data.get("news_impact", "UNCERTAIN")
    
    # RSI Logic
    if rsi > 70:
        rsi_text = "harganya sudah naik lumayan kencang, jadi ada kemungkinan dia bakal istirahat atau turun sebentar."
    elif rsi < 30:
        rsi_text = "harganya sudah turun cukup dalam, kadang ini bisa jadi momen pantulan."
    else:
        rsi_text = "tenaga harganya sekarang masih biasa-biasa saja, belum terlalu panas atau terlalu dingin."
        
    predicted_price = data.get("predicted_price_1d")
    price_text = f" (Target Harga: Rp {predicted_price:,.0f})" if predicted_price else ""
    
    # Prediction Logic
    if prediction == "UP" and pred_20d == "UP":
        pred_text = f"sistem komputer kita melihat tren harganya lagi bagus buat besok sampai sebulan ke depan{price_text},"
    elif prediction == "DOWN" and pred_20d == "DOWN":
        pred_text = f"sistem melihat tren harganya lagi kurang bagus, baik buat besok maupun sebulan ke depan{price_text},"
    elif prediction == "UP" and pred_20d == "DOWN":
        pred_text = f"meskipun besok ada potensi naik sebentar{price_text}, tapi sistem melihat sebulan ke depan trennya bisa agak berat,"
    elif prediction == "DOWN" and pred_20d == "UP":
        pred_text = f"walaupun besok diprediksi ada potensi turun{price_text}, tapi untuk sebulan ke depan sistem melihat ada harapan cerah,"
    else:
        pred_text = f"sistem belum melihat arah pergerakan yang jelas{price_text},"
        
    # Impact Logic
    if impact == "POSITIVE":
        news_text = "berita-berita terbaru di luar sana kelihatannya cukup mendukung."
    elif impact == "NEGATIVE":
        news_text = "ada beberapa berita kurang enak yang mungkin bikin harganya tertekan."
    elif impact == "MIXED":
        news_text = "beritanya campur-campur, ada yang bagus dan ada yang jelek."
    else:
        news_text = "beritanya belum terlalu ngasih dampak yang jelas ke perusahaan."
        
    explanation = (
        f"**Singkatnya:**\n\n"
        f"Untuk {ticker}, {rsi_text} Dari segi berita, {news_text} "
        f"Dan kalau dari kacamata prediksi, {pred_text} tapi ingat ya, ini cuma hasil hitung-hitungan sistem "
        f"dan bukan jaminan pasti bakal terjadi. Selalu siapin batasan risiko kalau mau coba-coba!"
    )
    
    return explanation
