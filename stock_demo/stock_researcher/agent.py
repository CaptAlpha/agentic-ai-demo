import yfinance as yf
from google.genai import types
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool


def get_stock_snapshot(ticker: str) -> dict:
    """Fetch current price, currency, market cap, P/E ratio, and 52-week range for a stock ticker."""
    try:
        stock = yf.Ticker(ticker.upper().strip())
        info = stock.info or {}
        fast = stock.fast_info
        price = getattr(fast, "last_price", None) or info.get("currentPrice")
        if price is None:
            return {"error": f"No market data found for '{ticker}'. Check ticker symbol (e.g., TCS.NS, NVDA)."}
        return {
            "ticker": ticker.upper(),
            "company": info.get("shortName", ticker.upper()),
            "currency": getattr(fast, "currency", info.get("currency", "USD")),
            "price": round(float(price), 2),
            "market_cap": info.get("marketCap"),
            "pe_ratio": round(float(info["trailingPE"]), 2) if info.get("trailingPE") else None,
            "52w_high": round(float(getattr(fast, "year_high", 0)), 2) or None,
            "52w_low": round(float(getattr(fast, "year_low", 0)), 2) or None,
        }
    except Exception as e:
        return {"error": f"Failed to fetch snapshot for {ticker}: {e}"}


def get_period_return(ticker: str, period: str = "6mo") -> dict:
    """Compute exact percentage price return over a period ('1mo', '3mo', '6mo', '1y')."""
    try:
        hist = yf.Ticker(ticker.upper().strip()).history(period=period)
        if hist.empty:
            return {"error": f"No historical data for '{ticker}' over '{period}'."}
        start_price = float(hist["Close"].iloc[0])
        end_price = float(hist["Close"].iloc[-1])
        pct_change = round(((end_price - start_price) / start_price) * 100, 2)
        return {
            "ticker": ticker.upper(),
            "period": period,
            "start_close": round(start_price, 2),
            "end_close": round(end_price, 2),
            "return_pct": pct_change,
        }
    except Exception as e:
        return {"error": f"Failed to compute return for {ticker}: {e}"}


MODEL = Gemini(
    model="gemini-3.5-flash-lite",  # Fallback options: "gemini-2.5-flash" or "gemini-3.8-flash"
    retry_options=types.HttpRetryOptions(
        attempts=5,
        initial_delay=2,
        exp_base=2,
        http_status_codes=[429, 503],
    ),
)

news_analyst = Agent(
    name="news_analyst",
    model=MODEL,
    description="Searches the live web for recent earnings, product launches, and risks for a company.",
    instruction="Use Google Search to summarize the top 3 recent news catalysts and key risks with dates.",
    tools=[google_search],
)

root_agent = Agent(
    name="stock_researcher",
    model=MODEL,
    instruction=(
        "You are a financial research assistant for students. For any stock question:\n"
        "1. Call get_stock_snapshot and get_period_return for quantitative facts.\n"
        "2. Delegate to news_analyst for recent earnings, catalysts, and risks.\n"
        "3. Present a crisp brief: Snapshot, Performance, Catalysts, Risks.\n"
        "Guardrail: Never give buy/sell investment advice; end with a 1-line educational disclaimer."
    ),
    tools=[get_stock_snapshot, get_period_return, AgentTool(agent=news_analyst)],
)