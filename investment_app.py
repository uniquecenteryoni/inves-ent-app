import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ========================
# Page Config & CSS
# ========================

st.set_page_config(page_title="כלי השקעות מקצועי", layout="wide", page_icon="📊")

RTL_CSS = """
<style>
    /* ---- Global RTL ---- */
    .stApp, .block-container { direction: rtl; text-align: right; }
    input, textarea, .stSelectbox, .stMultiSelect, .stNumberInput {
        direction: ltr; text-align: left;
    }
    [data-testid="stMetric"] { direction: ltr; text-align: center; }
    .stRadio > div { flex-direction: row-reverse; gap: 1rem; }
    .js-plotly-plot .plotly .modebar { direction: ltr; }
    .stTabs [data-baseweb="tab-list"] { direction: rtl; gap: 0.5rem; }

    /* ---- Tab styling ---- */
    .stTabs [data-baseweb="tab"] {
        padding: 0.6rem 1.6rem;
        border-radius: 10px 10px 0 0;
        font-size: 1rem;
        font-weight: 600;
    }

    /* ---- Section card ---- */
    .section-card {
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 1.5rem 1.3rem 1.2rem 1.3rem;
        background: linear-gradient(145deg, rgba(30,30,50,0.6) 0%, rgba(20,20,35,0.8) 100%);
        margin-bottom: 1rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    .section-card h4, .section-card h3 { margin-top: 0; }

    /* ---- Portfolio card ---- */
    .portfolio-frame {
        border: 2px solid #3a3a4a;
        border-radius: 14px;
        padding: 1.2rem 1rem 0.8rem 1rem;
        background: rgba(30,30,46,0.55);
        margin-bottom: 0.5rem;
    }

    /* ---- Result cards ---- */
    .result-card {
        border: 1px solid #3a3a4a;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        background: linear-gradient(135deg, rgba(30,30,46,0.7) 0%, rgba(20,20,35,0.9) 100%);
        text-align: center;
        margin-top: 0.3rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.1);
    }

    /* ---- Comparison box ---- */
    .comparison-box {
        border: 2px solid #4dabf7;
        border-radius: 14px;
        padding: 1.4rem 1.2rem;
        background: linear-gradient(135deg, rgba(77,171,247,0.08) 0%, rgba(30,30,46,0.6) 100%);
        margin-top: 1.2rem;
        margin-bottom: 0.8rem;
    }
    .comparison-box h3 { text-align: center; margin-bottom: 0.8rem; }

    /* ---- Recommendation section ---- */
    .reco-section-title { text-align: center; padding: 0.8rem 0; }
    .reco-badge {
        display: inline-block;
        padding: 0.2rem 0.7rem;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-left: 0.4rem;
    }
    .badge-green  { background: rgba(0,212,170,0.18);  color: #00d4aa; }
    .badge-yellow { background: rgba(255,204,0,0.18);  color: #ffcc00; }
    .badge-red    { background: rgba(255,107,107,0.18); color: #ff6b6b; }
    .badge-blue   { background: rgba(77,171,247,0.18);  color: #4dabf7; }
    .reco-detail { font-size: 0.93rem; color: #b0b0c0; line-height: 1.6; padding: 0.3rem 0; }
    .general-tip {
        border: 1px solid #3a3a4a;
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        background: rgba(30,30,46,0.45);
        margin-top: 0.4rem;
        margin-bottom: 0.3rem;
        font-size: 0.92rem;
        line-height: 1.65;
    }

    /* ---- Hero header ---- */
    .hero-header { text-align: center; padding: 1rem 0 0.3rem 0; }
    .hero-header h1 {
        font-size: 2.2rem;
        background: linear-gradient(90deg, #00d4aa, #4dabf7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .hero-subtitle {
        text-align: center;
        color: #888;
        font-size: 0.95rem;
        margin-bottom: 1rem;
    }
</style>
"""
st.markdown(RTL_CSS, unsafe_allow_html=True)

# ========================
# Session State Init
# ========================

if "num_portfolios" not in st.session_state:
    st.session_state.num_portfolios = 1

if "portfolios" not in st.session_state:
    st.session_state.portfolios = {}
    for i in range(3):
        st.session_state.portfolios[i] = {
            "assets": ["SPY"] if i == 0 else [],
            "weights": {"SPY": 100.0} if i == 0 else {},
            "phase": "שלב הצבירה",
            "monthly": 0,
            "withdrawal_rate": 0.0,
            "withdrawal_month": 1,
        }

# ========================
# Ticker Database
# ========================

TICKER_DB = {
    "AAPL": "Apple Inc.", "MSFT": "Microsoft Corp.",
    "GOOGL": "Alphabet (Google) Class A", "GOOG": "Alphabet (Google) Class C",
    "AMZN": "Amazon.com Inc.", "NVDA": "NVIDIA Corp.",
    "META": "Meta Platforms (Facebook)", "TSLA": "Tesla Inc.",
    "BRK-B": "Berkshire Hathaway B", "JPM": "JPMorgan Chase",
    "V": "Visa Inc.", "JNJ": "Johnson & Johnson",
    "WMT": "Walmart Inc.", "PG": "Procter & Gamble",
    "MA": "Mastercard Inc.", "UNH": "UnitedHealth Group",
    "HD": "Home Depot", "DIS": "Walt Disney Co.",
    "PYPL": "PayPal Holdings", "NFLX": "Netflix Inc.",
    "ADBE": "Adobe Inc.", "CRM": "Salesforce Inc.",
    "INTC": "Intel Corp.", "AMD": "Advanced Micro Devices",
    "CSCO": "Cisco Systems", "PEP": "PepsiCo Inc.",
    "KO": "Coca-Cola Co.", "ABT": "Abbott Laboratories",
    "MRK": "Merck & Co.", "NKE": "Nike Inc.",
    "T": "AT&T Inc.", "VZ": "Verizon Communications",
    "XOM": "Exxon Mobil Corp.", "CVX": "Chevron Corp.",
    "BA": "Boeing Co.", "CAT": "Caterpillar Inc.",
    "GS": "Goldman Sachs", "MS": "Morgan Stanley",
    "COST": "Costco Wholesale", "AVGO": "Broadcom Inc.",
    "QCOM": "Qualcomm Inc.", "TXN": "Texas Instruments",
    "NOW": "ServiceNow Inc.", "UBER": "Uber Technologies",
    "SQ": "Block Inc. (Square)", "SHOP": "Shopify Inc.",
    "SNOW": "Snowflake Inc.", "PLTR": "Palantir Technologies",
    "COIN": "Coinbase Global", "SOFI": "SoFi Technologies",
    "RIVN": "Rivian Automotive", "LCID": "Lucid Group",
    "SPY": "SPDR S&P 500 ETF", "VOO": "Vanguard S&P 500 ETF",
    "IVV": "iShares Core S&P 500 ETF", "QQQ": "Invesco Nasdaq 100 ETF",
    "VTI": "Vanguard Total US Market ETF", "IWM": "iShares Russell 2000 ETF",
    "DIA": "SPDR Dow Jones Industrial ETF", "VUG": "Vanguard Growth ETF",
    "VTV": "Vanguard Value ETF", "SCHD": "Schwab US Dividend Equity ETF",
    "VIG": "Vanguard Dividend Appreciation ETF",
    "ARKK": "ARK Innovation ETF", "ARKW": "ARK Next Gen Internet ETF",
    "XLK": "Technology Select Sector SPDR", "XLF": "Financial Select Sector SPDR",
    "XLE": "Energy Select Sector SPDR", "XLV": "Health Care Select Sector SPDR",
    "XLY": "Consumer Discretionary SPDR", "XLP": "Consumer Staples SPDR",
    "XLI": "Industrial Select Sector SPDR", "XLRE": "Real Estate Select Sector SPDR",
    "VXUS": "Vanguard Total International Stock ETF",
    "EFA": "iShares MSCI EAFE ETF", "EEM": "iShares MSCI Emerging Markets ETF",
    "VWO": "Vanguard FTSE Emerging Markets ETF",
    "VEA": "Vanguard FTSE Developed Markets ETF",
    "IEMG": "iShares Core MSCI Emerging Markets ETF",
    "FXI": "iShares China Large-Cap ETF", "EWJ": "iShares MSCI Japan ETF",
    "EWG": "iShares MSCI Germany ETF", "EWU": "iShares MSCI United Kingdom ETF",
    "BND": "Vanguard Total Bond Market ETF",
    "AGG": "iShares Core US Aggregate Bond ETF",
    "TLT": "iShares 20+ Year Treasury Bond ETF",
    "IEF": "iShares 7-10 Year Treasury Bond ETF",
    "SHY": "iShares 1-3 Year Treasury Bond ETF",
    "TIP": "iShares TIPS Bond ETF",
    "LQD": "iShares Investment Grade Corporate Bond ETF",
    "HYG": "iShares iBoxx High Yield Corporate Bond ETF",
    "BIL": "SPDR Bloomberg 1-3 Month T-Bill ETF",
    "BNDX": "Vanguard Total International Bond ETF",
    "EMB": "iShares J.P. Morgan USD EM Bond ETF",
    "GLD": "SPDR Gold Shares", "IAU": "iShares Gold Trust",
    "SLV": "iShares Silver Trust", "USO": "United States Oil Fund",
    "DBC": "Invesco DB Commodity Index ETF",
    "VNQ": "Vanguard Real Estate ETF", "IYR": "iShares US Real Estate ETF",
    "VNQI": "Vanguard Global ex-US Real Estate ETF",
    "NICE": "NICE Ltd.", "CYBR": "CyberArk Software",
    "CHKP": "Check Point Software", "WIX": "Wix.com Ltd.",
    "MNDY": "monday.com Ltd.", "GLBE": "Global-e Online",
    "FVRR": "Fiverr International", "RSKD": "Riskified Ltd.",
    "BTC-USD": "Bitcoin USD", "ETH-USD": "Ethereum USD",
    "MSTR": "MicroStrategy (Bitcoin proxy)",
    "BITO": "ProShares Bitcoin Strategy ETF",
    "IBIT": "iShares Bitcoin Trust ETF",
}

PERIOD_MAP = {
    "יום": "1d", "שבוע": "5d", "חודש": "1mo",
    "מתחילת השנה": "ytd", "שנה": "1y", "5 שנים": "5y",
}

MONTHS_HEB = {
    1: "ינואר", 2: "פברואר", 3: "מרס", 4: "אפריל",
    5: "מאי", 6: "יוני", 7: "יולי", 8: "אוגוסט",
    9: "ספטמבר", 10: "אוקטובר", 11: "נובמבר", 12: "דצמבר",
}


def search_tickers(query: str, limit: int = 12) -> list[tuple[str, str]]:
    if not query:
        return []
    q = query.upper().strip()
    exact, starts, contains = [], [], []
    for sym, name in TICKER_DB.items():
        sym_up, name_up = sym.upper(), name.upper()
        if sym_up == q:
            exact.append((sym, name))
        elif sym_up.startswith(q) or name_up.startswith(q):
            starts.append((sym, name))
        elif q in sym_up or q in name_up:
            contains.append((sym, name))
    return (exact + starts + contains)[:limit]


# ========================
# Data Functions
# ========================

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_price_history(ticker: str, period: str) -> pd.DataFrame:
    try:
        tk = yf.Ticker(ticker)
        interval = "5m" if period == "1d" else ("60m" if period == "5d" else "1d")
        df = tk.history(period=period, interval=interval, auto_adjust=True)
        if df.empty:
            return pd.DataFrame()
        return df[["Close"]]
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def download_close_prices(tickers: tuple, start_date: str, end_date: str) -> pd.DataFrame:
    try:
        data = yf.download(list(tickers), start=start_date, end=end_date, auto_adjust=True, progress=False)
        if data.empty:
            return pd.DataFrame()
        if len(tickers) == 1:
            closes = data[["Close"]]
            closes.columns = [tickers[0]]
        else:
            closes = data["Close"]
        return closes
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=86400, show_spinner=False)
def get_usd_to_ils() -> float:
    try:
        tk = yf.Ticker("USDILS=X")
        data = tk.history(period="5d")
        if not data.empty:
            return float(data["Close"].iloc[-1])
    except Exception:
        pass
    return 3.6


def format_currency(value: float, cur: str) -> str:
    if cur == "ILS":
        return f"₪{value:,.0f}"
    return f"${value:,.0f}"


# ================================================================
#   HERO HEADER
# ================================================================

st.markdown('<div class="hero-header"><h1>📊 כלי השקעות מקצועי</h1></div>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">ניתוח מניות • סימולציית תיקים • השוואת אסטרטגיות • חישוב מס רווחי הון</p>', unsafe_allow_html=True)

# ================================================================
#   MAIN TABS
# ================================================================

tab_research, tab_simulation = st.tabs(["🔍 ניתוח מניות", "💰 סימולציית תיקים"])

# ================================================================
#   TAB 1 — Stock Research
# ================================================================

with tab_research:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### 🔎 חיפוש וניתוח נכסים")

    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        search_query = st.text_input("הקלד סימול או שם חברה", placeholder="למשל: AAPL, Tesla, Gold, QQQ …", key="global_search")
    with search_col2:
        search_period = st.radio("תקופה", list(PERIOD_MAP.keys()), index=4, horizontal=True, key="search_period")

    if search_query:
        matches = search_tickers(search_query)
        if matches:
            options_list = [f"{sym}  —  {name}" for sym, name in matches]
            chosen = st.selectbox("תוצאות תואמות — בחר נכס:", options=options_list, key="search_select")
            chosen_ticker = chosen.split("  —  ")[0].strip() if chosen else None
        else:
            chosen_ticker = search_query.strip().upper()
            st.info(f"לא נמצא במאגר — מנסה לטעון: {chosen_ticker}")

        if chosen_ticker:
            with st.spinner("טוען נתונים..."):
                price_data = fetch_price_history(chosen_ticker, PERIOD_MAP[search_period])

            if not price_data.empty:
                try:
                    asset_name = yf.Ticker(chosen_ticker).info.get("shortName", chosen_ticker)
                except Exception:
                    asset_name = chosen_ticker

                st.markdown(f"#### {asset_name} ({chosen_ticker})")

                fig_s = go.Figure()
                fig_s.add_trace(go.Scatter(
                    x=price_data.index, y=price_data["Close"],
                    mode="lines", name=chosen_ticker,
                    line=dict(color="#00d4aa", width=2),
                    fill="tozeroy", fillcolor="rgba(0,212,170,0.1)",
                ))
                fig_s.update_layout(
                    template="plotly_dark", height=400,
                    margin=dict(l=20, r=20, t=30, b=20),
                    xaxis_title="תאריך", yaxis_title="מחיר ($)",
                    hovermode="x unified",
                )
                st.plotly_chart(fig_s, use_container_width=True)

                fp = float(price_data["Close"].iloc[0])
                lp = float(price_data["Close"].iloc[-1])
                ch = ((lp - fp) / fp) * 100
                hi = float(price_data["Close"].max())
                lo = float(price_data["Close"].min())

                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("מחיר נוכחי", f"${lp:.2f}")
                mc2.metric("שינוי בתקופה", f"{ch:+.2f}%")
                mc3.metric("שיא", f"${hi:.2f}")
                mc4.metric("שפל", f"${lo:.2f}")
            else:
                st.warning(f"לא נמצאו נתונים עבור: {chosen_ticker}")

    st.markdown('</div>', unsafe_allow_html=True)

# ================================================================
#   TAB 2 — Portfolio Simulation
# ================================================================

with tab_simulation:

    # ── SECTION: Global Settings ──
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### ⚙️ הגדרות כלליות")

    # Row 1: Currency, Tax, Rebalance
    cur_col, tax_col, rebal_col = st.columns(3)
    with cur_col:
        currency = st.radio("💱 מטבע", ["USD ($)", "ILS (₪)"], horizontal=True, key="currency_toggle")
        active_currency = "ILS" if "ILS" in currency else "USD"
    with tax_col:
        capital_gains_tax_pct = st.number_input(
            "🏛️ מס רווחי הון (%)", min_value=0.0, max_value=50.0,
            value=25.0, step=0.5, key="cg_tax_pct",
            help="אחוז המס על רווחי הון. ברירת מחדל: 25% (ישראל).",
        )
    with rebal_col:
        rebalance_freq = st.selectbox("🔄 איזון מחדש", ["ללא", "חודשי", "רבעוני", "שנתי"], key="rebalance_freq")

    CAPITAL_GAINS_TAX = capital_gains_tax_pct / 100.0
    freq_map = {"ללא": None, "חודשי": "ME", "רבעוני": "QE", "שנתי": "YE"}
    exchange_rate = get_usd_to_ils() if active_currency == "ILS" else 1.0
    cur_symbol = "₪" if active_currency == "ILS" else "$"
    cur_label = "שקלים" if active_currency == "ILS" else "דולרים"

    st.markdown("---")

    # Row 2: Investment amounts (currency-aware)
    inv_col1, inv_col2 = st.columns(2)
    with inv_col1:
        initial_capital_input = st.number_input(
            f"💵 סכום השקעה ראשוני ({cur_symbol})",
            min_value=0, max_value=100_000_000,
            value=100_000, step=10_000, key="initial_capital",
            help=f"סכום חד-פעמי ב{cur_label}. הסימולציה מחשבת בדולרים.",
        )
    with inv_col2:
        global_monthly_input = st.number_input(
            f"📆 הפקדה חודשית ({cur_symbol})",
            min_value=0, max_value=1_000_000,
            value=0, step=500, key="global_monthly",
            help=f"הפקדה חודשית קבועה ב{cur_label}.",
        )

    # Convert to USD for simulation
    if active_currency == "ILS":
        initial_capital = initial_capital_input / exchange_rate
        global_monthly = global_monthly_input / exchange_rate
    else:
        initial_capital = float(initial_capital_input)
        global_monthly = float(global_monthly_input)

    if active_currency == "ILS":
        st.caption(
            f"💱 שער המרה: {exchange_rate:.2f} ₪/$ | "
            f"השקעה ראשונית: ${initial_capital:,.0f} | "
            f"הפקדה חודשית: ${global_monthly:,.0f}"
        )

    st.markdown("---")

    # Row 3: Time range
    st.markdown("**📅 טווח זמן**")
    current_year = datetime.today().year
    dr1, dr2 = st.columns(2)
    with dr1:
        start_year = st.number_input("משנת", min_value=1990, max_value=current_year + 20, value=current_year - 10, step=1, key="start_year")
    with dr2:
        end_year = st.number_input("עד שנת", min_value=int(start_year) + 1, max_value=current_year + 30, value=max(int(start_year) + 10, current_year), step=1, key="end_year")

    is_future = int(end_year) > current_year
    if is_future:
        st.info(f"⏳ טווח הסימולציה כולל שנים עתידיות ({current_year + 1}–{int(end_year)}). הפרויקציה מבוססת על תשואות היסטוריות ממוצעות.")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── SECTION: Portfolio Definition ──
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### 📁 הגדרת פורטפוליו להשוואה")

    add_col, remove_col, info_col = st.columns([1, 1, 2])
    with add_col:
        if st.button("➕ הוסף פורטפוליו", disabled=(st.session_state.num_portfolios >= 3)):
            st.session_state.num_portfolios += 1
            new_idx = st.session_state.num_portfolios - 1
            if new_idx not in st.session_state.portfolios:
                st.session_state.portfolios[new_idx] = {
                    "assets": [], "weights": {}, "phase": "שלב הצבירה",
                    "monthly": 0, "withdrawal_rate": 0.0, "withdrawal_month": 1,
                }
            st.rerun()
    with remove_col:
        if st.button("➖ הסר פורטפוליו", disabled=(st.session_state.num_portfolios <= 1)):
            st.session_state.num_portfolios -= 1
            st.rerun()
    with info_col:
        st.caption(f"מוצגים {st.session_state.num_portfolios} מתוך 3 פורטפוליו מקסימום")

    ASSET_OPTIONS = sorted(TICKER_DB.keys())
    num_p = st.session_state.num_portfolios
    portfolio_cols = st.columns(num_p)

    def render_portfolio(col, idx):
        with col:
            st.markdown('<div class="portfolio-frame">', unsafe_allow_html=True)
            st.markdown(f"#### 📌 פורטפוליו {idx + 1}")

            phase = st.radio("שלב", ["שלב הצבירה", "שלב המשיכה / פרישה"], key=f"phase_{idx}", horizontal=True)

            withdrawal_rate = 0.0
            withdrawal_month = 1
            if "משיכה" in phase or "פרישה" in phase:
                withdrawal_rate = st.number_input(
                    "📤 אחוז משיכה שנתי (%)", min_value=0.0, max_value=20.0,
                    value=4.0, step=0.5, key=f"wd_{idx}",
                    help="הכסף ימשך מתוך התיק פעם בשנה בחודש שתבחר.",
                )
                withdrawal_month = st.selectbox(
                    "📅 חודש משיכה", options=list(MONTHS_HEB.keys()),
                    format_func=lambda m: f"{MONTHS_HEB[m]} ({m})",
                    index=0, key=f"wd_month_{idx}",
                    help=f"באיזה חודש בשנה תתבצע המשיכה ({capital_gains_tax_pct:.0f}% מס רווחי הון ינוכה מהרווח).",
                )
                st.caption(f"💰 {capital_gains_tax_pct:.0f}% מס רווחי הון ינוכה אוטומטית מחלק הרווח במשיכה")

            selected_assets = st.multiselect(
                "🔎 בחר נכסים / מניות", options=ASSET_OPTIONS,
                default=st.session_state.portfolios[idx].get("assets", []),
                key=f"assets_{idx}",
                format_func=lambda x: f"{x} — {TICKER_DB.get(x, '')}",
            )

            custom_ticker = st.text_input("➕ הוסף סימול ידנית (מופרד בפסיק)", placeholder="SOXX, KWEB …", key=f"custom_{idx}")
            if custom_ticker:
                for part in custom_ticker.split(","):
                    ct = part.strip().upper()
                    if ct and ct not in selected_assets:
                        selected_assets.append(ct)

            weights = {}
            if selected_assets:
                st.markdown("**⚖️ הקצאת אחוזים (%)**")
                default_w = round(100.0 / len(selected_assets), 1)
                for asset in selected_assets:
                    prev = st.session_state.portfolios[idx].get("weights", {}).get(asset, default_w)
                    w = st.number_input(f"{asset}", min_value=0.0, max_value=100.0, value=min(prev, 100.0), step=5.0, key=f"w_{idx}_{asset}")
                    weights[asset] = w

                total_w = sum(weights.values())
                if abs(total_w - 100.0) < 0.01:
                    st.success(f"✅ סה״כ: {total_w:.1f}%")
                elif total_w > 100:
                    st.error(f"🚫 סה״כ: {total_w:.1f}% — חרגת!")
                else:
                    st.warning(f"⚠️ סה״כ: {total_w:.1f}% (צריך 100%)")
            else:
                st.info("בחר לפחות נכס אחד")

            st.markdown("</div>", unsafe_allow_html=True)

            st.session_state.portfolios[idx] = {
                "assets": selected_assets, "weights": weights,
                "phase": phase, "monthly": 0,
                "withdrawal_rate": withdrawal_rate, "withdrawal_month": withdrawal_month,
            }

    for idx in range(num_p):
        render_portfolio(portfolio_cols[idx], idx)

    st.markdown('</div>', unsafe_allow_html=True)

    # ================================================================
    #   Simulation Engine
    # ================================================================

    def simulate_portfolio(port_cfg, initial, monthly_contribution, start_y, end_y, rebalance):
        assets = port_cfg["assets"]
        weights_dict = port_cfg["weights"]
        withdrawal_rate = port_cfg.get("withdrawal_rate", 0.0)
        withdrawal_month = port_cfg.get("withdrawal_month", 1)

        if not assets or not weights_dict:
            return pd.Series(dtype=float), {}
        total_w = sum(weights_dict.values())
        if total_w == 0:
            return pd.Series(dtype=float), {}

        norm_weights = np.array([weights_dict.get(a, 0) / total_w for a in assets])
        today = datetime.today()
        sim_start = datetime(int(start_y), 1, 1)
        sim_end = datetime(int(end_y), 12, 31)

        hist_end = min(sim_end, today)
        dl_start = sim_start if sim_start < today else today - timedelta(days=10 * 365)

        closes = download_close_prices(tuple(assets), dl_start.strftime("%Y-%m-%d"), hist_end.strftime("%Y-%m-%d"))
        if closes.empty:
            return pd.Series(dtype=float), {}

        missing = [a for a in assets if a not in closes.columns]
        if missing:
            return pd.Series(dtype=float), {}

        closes = closes[list(assets)]
        returns_df = closes.pct_change().dropna()
        if returns_df.empty:
            return pd.Series(dtype=float), {}

        port_daily_returns = (returns_df * norm_weights).sum(axis=1)
        hist_returns = port_daily_returns[port_daily_returns.index >= pd.Timestamp(sim_start)]

        if sim_end > today:
            mean_daily = port_daily_returns.mean()
            std_daily = port_daily_returns.std()
            future_days = pd.bdate_range(start=today + timedelta(days=1), end=sim_end)
            np.random.seed(42)
            future_returns = np.random.normal(mean_daily, std_daily, len(future_days))
            combined_returns = pd.concat([hist_returns, pd.Series(future_returns, index=future_days)])
        else:
            combined_returns = hist_returns

        if rebalance:
            combined_returns = combined_returns.resample(rebalance).apply(lambda x: (1 + x).prod() - 1)

        capital = float(initial)
        cost_basis = float(initial)
        total_invested = float(initial)
        total_withdrawn_gross = 0.0
        total_tax_paid = 0.0
        total_withdrawn_net = 0.0
        values = []
        prev_month = None
        withdrew_this_year = set()

        for date, r in combined_returns.items():
            cur_month = (date.year, date.month)
            new_month = prev_month is not None and cur_month != prev_month
            prev_month = cur_month
            capital *= (1 + r)

            if new_month:
                if monthly_contribution > 0:
                    capital += monthly_contribution
                    cost_basis += monthly_contribution
                    total_invested += monthly_contribution

                if withdrawal_rate > 0 and date.month == withdrawal_month and date.year not in withdrew_this_year:
                    withdrew_this_year.add(date.year)
                    gross_wd = capital * (withdrawal_rate / 100.0)

                    if capital > 0 and capital > cost_basis:
                        gain_ratio = (capital - cost_basis) / capital
                        tax = gross_wd * gain_ratio * CAPITAL_GAINS_TAX
                    else:
                        tax = 0.0

                    total_withdrawn_gross += gross_wd
                    total_tax_paid += tax
                    total_withdrawn_net += gross_wd - tax

                    capital -= gross_wd
                    capital = max(capital, 0)

                    if capital > 0:
                        cost_basis *= capital / (capital + gross_wd) if (capital + gross_wd) > 0 else 0
                    else:
                        cost_basis = 0

            values.append(capital)

        if not values:
            return pd.Series(dtype=float), {}

        series = pd.Series(values, index=combined_returns.index)
        start_val = float(initial)
        end_val = series.iloc[-1]
        n_years = max((series.index[-1] - series.index[0]).days / 365.25, 0.01)
        total_return_pct = ((end_val / start_val) - 1) * 100 if start_val > 0 else 0
        cagr = ((end_val / start_val) ** (1 / n_years) - 1) * 100 if start_val > 0 else 0
        daily_ret = series.pct_change().dropna()
        ann_vol = daily_ret.std() * np.sqrt(252) * 100
        sharpe = (daily_ret.mean() / daily_ret.std() * np.sqrt(252)) if daily_ret.std() > 0 else 0
        cumulative = (1 + daily_ret).cumprod()
        peak = cumulative.cummax()
        max_dd = ((cumulative - peak) / peak).min() * 100 if len(cumulative) > 0 else 0

        return series, {
            "start_val": start_val, "end_val": end_val,
            "total_invested": total_invested, "cost_basis": cost_basis,
            "total_return_pct": total_return_pct, "cagr": cagr,
            "ann_vol": ann_vol, "sharpe": sharpe, "max_dd": max_dd,
            "n_years": n_years,
            "total_withdrawn_gross": total_withdrawn_gross,
            "total_tax_paid": total_tax_paid,
            "total_withdrawn_net": total_withdrawn_net,
        }

    # ================================================================
    #   Recommendation Engine
    # ================================================================

    def render_recommendations(all_stats, portfolios_cfg, initial, monthly):
        if not all_stats:
            return

        st.markdown("---")
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="reco-section-title">', unsafe_allow_html=True)
        st.markdown("### 💡 המלצות מקצועיות")
        st.markdown('</div>', unsafe_allow_html=True)

        if len(all_stats) > 1:
            best_sharpe = max(range(len(all_stats)), key=lambda i: all_stats[i]["sharpe"])
            best_return = max(range(len(all_stats)), key=lambda i: all_stats[i]["total_return_pct"])
            lowest_vol = min(range(len(all_stats)), key=lambda i: all_stats[i]["ann_vol"])

            tc = st.columns(3)
            with tc[0]:
                st.markdown(f'<div class="general-tip" style="text-align:center;">🏆 <b>שארפ הטוב ביותר</b><br>פורטפוליו {best_sharpe + 1} &nbsp;<span class="reco-badge badge-green">{all_stats[best_sharpe]["sharpe"]:.2f}</span></div>', unsafe_allow_html=True)
            with tc[1]:
                st.markdown(f'<div class="general-tip" style="text-align:center;">📈 <b>תשואה גבוהה ביותר</b><br>פורטפוליו {best_return + 1} &nbsp;<span class="reco-badge badge-blue">{all_stats[best_return]["total_return_pct"]:.1f}%</span></div>', unsafe_allow_html=True)
            with tc[2]:
                st.markdown(f'<div class="general-tip" style="text-align:center;">🛡️ <b>סיכון נמוך ביותר</b><br>פורטפוליו {lowest_vol + 1} &nbsp;<span class="reco-badge badge-yellow">{all_stats[lowest_vol]["ann_vol"]:.1f}%</span></div>', unsafe_allow_html=True)
            st.markdown("")

        for i, stats in enumerate(all_stats):
            pcfg = portfolios_cfg[i]
            n_assets = len(pcfg["assets"])
            phase = pcfg["phase"]
            sharpe = stats["sharpe"]
            vol = stats["ann_vol"]
            dd = stats["max_dd"]
            is_wd = "משיכה" in phase or "פרישה" in phase

            if n_assets == 1:
                div_badge = '<span class="reco-badge badge-red">פיזור נמוך</span>'
            elif n_assets <= 3:
                div_badge = '<span class="reco-badge badge-yellow">פיזור בינוני</span>'
            else:
                div_badge = '<span class="reco-badge badge-green">פיזור טוב</span>'

            sharpe_badge = '<span class="reco-badge badge-green">שארפ מצוין</span>' if sharpe > 0.8 else ('<span class="reco-badge badge-yellow">שארפ סביר</span>' if sharpe > 0.4 else '<span class="reco-badge badge-red">שארפ נמוך</span>')
            risk_badge = '<span class="reco-badge badge-red">סיכון גבוה</span>' if vol > 25 else ('<span class="reco-badge badge-yellow">סיכון בינוני</span>' if vol > 15 else '<span class="reco-badge badge-green">סיכון נמוך</span>')

            phase_icon = "🏦" if is_wd else "📈"
            phase_label = "שלב משיכה" if is_wd else "שלב צבירה"
            header_html = f'{phase_icon} <b>פורטפוליו {i+1}</b> &mdash; {phase_label}&nbsp;&nbsp; {div_badge} {sharpe_badge} {risk_badge}'

            with st.expander(f"📌 פורטפוליו {i+1} — {phase_label}  |  שארפ {sharpe:.2f}  |  תנודתיות {vol:.1f}%"):
                st.markdown(header_html, unsafe_allow_html=True)
                st.markdown("")
                d1, d2, d3 = st.columns(3)
                with d1:
                    st.metric("שארפ", f"{sharpe:.2f}")
                with d2:
                    st.metric("תנודתיות שנתית", f"{vol:.1f}%")
                with d3:
                    st.metric("ירידה מקסימלית", f"{dd:.1f}%")
                st.markdown("")

                if n_assets == 1:
                    st.warning("⚠️ **פיזור נמוך מאוד** — נכס בודד. מומלץ להוסיף ETF רחב (VTI/VXUS) ואג״ח (BND).")
                elif n_assets <= 3:
                    st.info("🔶 **פיזור בינוני** — שקול להוסיף 2-3 אפיקים נוספים להקטנת סיכון.")
                else:
                    st.success("✅ **פיזור טוב** — מגוון נכסים בתיק.")

                if vol > 25:
                    st.markdown('<div class="reco-detail">🔴 תנודתיות גבוהה מתאימה למשקיע אגרסיבי עם אופק ארוך.</div>', unsafe_allow_html=True)
                elif vol > 15:
                    st.markdown('<div class="reco-detail">🟡 תנודתיות בינונית — סיכון מאוזן, דורש משמעת בירידות.</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="reco-detail">🟢 תנודתיות נמוכה — שמרני, מתאים ליציבות.</div>', unsafe_allow_html=True)

                if dd < -30:
                    st.markdown(f'<div class="reco-detail">⚠️ ירידה מקסימלית חמורה ({dd:.1f}%) — ודא שתעמוד בזה מבלי למכור בפאניקה.</div>', unsafe_allow_html=True)

                st.markdown("")
                if is_wd:
                    st.markdown('<div class="general-tip">🏦 <b>שלב פרישה</b> — העדף אג״ח ודיבידנדים. 3-4% משיכה שנתית נחשבת בת-קיימא.</div>', unsafe_allow_html=True)
                    wd_rate = pcfg.get("withdrawal_rate", 0)
                    if wd_rate > 5:
                        st.error(f"⚠️ משיכה של {wd_rate}% גבוהה — סיכון למיצוי הקרן. שקול 3.5-4%.")
                    tax_paid = stats.get("total_tax_paid", 0)
                    total_wd_gross = stats.get("total_withdrawn_gross", 0)
                    if tax_paid > 0 and total_wd_gross > 0:
                        tax_ratio = tax_paid / total_wd_gross * 100
                        st.markdown(f'<div class="general-tip">🏛️ <b>מיסוי</b>: שולם {tax_ratio:.1f}% מס אפקטיבי על המשיכות ({capital_gains_tax_pct:.0f}% על חלק הרווח בלבד).<br>💡 <b>טיפ</b>: שקול משיכה בשנים שבהן הרווח נמוך יותר. קופות גמל/קרן השתלמות מאפשרות דחיית/פטור מס.</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="general-tip">📈 <b>שלב צבירה</b> — אופק ארוך מאפשר חשיפה גבוהה למניות. DCA (הפקדה חודשית) מפחית סיכון תזמון.</div>', unsafe_allow_html=True)
                    if monthly == 0:
                        st.info("💡 לא הגדרת הפקדה חודשית — גם סכום קטן ישפר משמעותית את התוצאה.")

        st.markdown("")
        st.markdown("#### 🧭 עקרונות כלליים")
        tips = [
            ("🌐 גיוון", "שלב מניות, אג״ח, וסחורות להקטנת סיכון."),
            ("⚖️ איזון מחדש", "רבעוני/שנתי שומר על רמת הסיכון הרצויה."),
            ("💸 עלויות", "העדף ETF עם Expense Ratio < 0.2%."),
            ("🧠 משמעת", "הישאר עם התוכנית גם בירידות."),
            (f"🏛️ מיסוי", f"{capital_gains_tax_pct:.0f}% מס רווחי הון. קופ״ג/קרן השתלמות/IRA מאפשרים דחיית/פטור מס."),
        ]
        tip_cols = st.columns(len(tips))
        for j, (title, body) in enumerate(tips):
            with tip_cols[j]:
                st.markdown(f'<div class="general-tip" style="text-align:center; min-height:110px;"><b>{title}</b><br><span style="font-size:0.85rem; color:#b0b0c0;">{body}</span></div>', unsafe_allow_html=True)

        st.caption("⚠️ ניתוח טכני בלבד — אינו מהווה ייעוץ השקעות. התייעץ עם יועץ מוסמך.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ================================================================
    #   Bottom-line Comparison
    # ================================================================

    def render_bottom_line_comparison(all_stats_raw, portfolios_cfg, num_p_loc, ex_rate, cur, tax_rate):
        if len(all_stats_raw) < 2:
            return

        cur_sym = "₪" if cur == "ILS" else "$"
        tax_pct_display = f"{tax_rate * 100:.0f}%"
        n = min(num_p_loc, len(all_stats_raw))

        net_profits, tax_totals, total_invested_arr, annual_pcts, detail_rows = [], [], [], [], []

        for i in range(n):
            s = all_stats_raw[i]
            phase = portfolios_cfg[i]["phase"]
            end_val = s["end_val"]
            total_invested = s["total_invested"]
            n_years = s.get("n_years", 1)
            is_wd = "משיכה" in phase or "פרישה" in phase

            if is_wd:
                cash_net = s.get("total_withdrawn_net", 0)
                ongoing_tax = s.get("total_tax_paid", 0)
                sim_cost_basis = s.get("cost_basis", 0)
                remaining_gain = max(end_val - sim_cost_basis, 0)
                final_sale_tax = remaining_gain * tax_rate
                net_remaining_profit = remaining_gain - final_sale_tax
                net_profit = cash_net + net_remaining_profit
                total_tax = ongoing_tax + final_sale_tax
                detail_rows.append({"phase_label": "משיכה", "total_invested": total_invested, "end_val": end_val, "cash_withdrawn_net": cash_net, "remaining_gain_net": net_remaining_profit, "ongoing_tax": ongoing_tax, "final_sale_tax": final_sale_tax, "total_tax": total_tax, "net_profit": net_profit})
            else:
                gain = max(end_val - total_invested, 0)
                final_sale_tax = gain * tax_rate
                net_profit = gain - final_sale_tax
                total_tax = final_sale_tax
                detail_rows.append({"phase_label": "צבירה", "total_invested": total_invested, "end_val": end_val, "cash_withdrawn_net": 0, "remaining_gain_net": net_profit, "ongoing_tax": 0, "final_sale_tax": final_sale_tax, "total_tax": total_tax, "net_profit": net_profit})

            if total_invested > 0 and n_years > 0:
                total_end_net = total_invested + net_profit
                ann_net = ((total_end_net / total_invested) ** (1 / n_years) - 1) * 100 if total_end_net > 0 else -100.0
            else:
                ann_net = 0.0

            net_profits.append(net_profit * ex_rate)
            tax_totals.append(total_tax * ex_rate)
            total_invested_arr.append(total_invested * ex_rate)
            annual_pcts.append(ann_net)

        st.markdown("---")
        st.markdown('<div class="comparison-box">', unsafe_allow_html=True)
        st.markdown("### 📐 השוואת רווח נטו — כמה באמת הרווחת?")
        st.caption(f"רווח נטו = משיכות נטו + רווח נטו שנותר בתיק — אחרי {tax_pct_display} מס רווחי הון")

        metric_cols = st.columns(n)
        best_idx = max(range(n), key=lambda i: net_profits[i])

        for i in range(n):
            d = detail_rows[i]
            badge = " 👑" if i == best_idx else ""
            roi = (net_profits[i] / total_invested_arr[i] * 100) if total_invested_arr[i] > 0 else 0
            with metric_cols[i]:
                st.metric(
                    label=f"פורטפוליו {i+1} ({d['phase_label']}){badge}",
                    value=f"{cur_sym}{net_profits[i]:,.0f}",
                    delta=f"תשואה נטו כוללת: {roi:.1f}% | שנתי: ~{annual_pcts[i]:.1f}%",
                    help=f"סה״כ הושקע: {cur_sym}{total_invested_arr[i]:,.0f}\nסה״כ מס: {cur_sym}{tax_totals[i]:,.0f}",
                )

        if n == 2:
            delta = net_profits[0] - net_profits[1]
            delta_pct = (delta / abs(net_profits[1]) * 100) if net_profits[1] != 0 else 0
            ann_diff = annual_pcts[0] - annual_pcts[1]
            winner = f"לטובת פורטפוליו 1 ({detail_rows[0]['phase_label']})" if delta > 0 else f"לטובת פורטפוליו 2 ({detail_rows[1]['phase_label']})"
            g1c, g2c = st.columns(2)
            with g1c:
                st.metric(label="הפרש ברווח הנטו (Δ)", value=f"{cur_sym}{abs(delta):,.0f}", delta=f"{abs(delta_pct):.1f}% {winner}", delta_color="normal" if delta > 0 else "inverse")
            with g2c:
                st.metric(label="הפרש תשואה שנתית נטו (Δ)", value=f"{abs(ann_diff):.2f}%", delta=f"{winner}", delta_color="normal" if delta > 0 else "inverse")

        st.markdown("")
        st.markdown("#### 📋 טבלת סיכום")

        row_labels = ["סה״כ הושקע", "שווי תיק סופי", "משיכות נטו (אם יש)", "רווח נטו שנותר בתיק", f"מס על משיכות ({tax_pct_display})", f"מס על יתרת תיק ({tax_pct_display})", f"סה״כ מס ({tax_pct_display})", "✅ רווח נטו כולל", "📊 תשואה שנתית נטו מוערכת"]
        table_data = {"מדד": row_labels}

        for i in range(n):
            d = detail_rows[i]
            table_data[f"פורטפוליו {i+1} ({d['phase_label']})"] = [
                f"{cur_sym}{d['total_invested'] * ex_rate:,.0f}",
                f"{cur_sym}{d['end_val'] * ex_rate:,.0f}",
                f"{cur_sym}{d['cash_withdrawn_net'] * ex_rate:,.0f}" if d['cash_withdrawn_net'] > 0 else "—",
                f"{cur_sym}{d['remaining_gain_net'] * ex_rate:,.0f}",
                f"{cur_sym}{d['ongoing_tax'] * ex_rate:,.0f}" if d['ongoing_tax'] > 0 else "—",
                f"{cur_sym}{d['final_sale_tax'] * ex_rate:,.0f}",
                f"{cur_sym}{tax_totals[i]:,.0f}",
                f"{cur_sym}{net_profits[i]:,.0f}",
                f"~{annual_pcts[i]:.2f}%",
            ]

        st.dataframe(pd.DataFrame(table_data).set_index("מדד"), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ──────────────────────────────────
    #  Run Simulation
    # ──────────────────────────────────

    st.markdown("")
    if st.button("🚀 הפעל סימולציה", use_container_width=True, type="primary"):

        fig = go.Figure()
        all_display_metrics = []
        all_stats_raw = []
        colors = ["#00d4aa", "#ff6b6b", "#4dabf7"]
        any_data = False

        for idx in range(num_p):
            pcfg = st.session_state.portfolios[idx]
            series, stats = simulate_portfolio(pcfg, initial_capital, global_monthly, start_year, end_year, freq_map[rebalance_freq])
            if series.empty:
                continue

            any_data = True
            disp = series * exchange_rate
            fig.add_trace(go.Scatter(x=disp.index, y=disp.values, mode="lines", name=f"פורטפוליו {idx + 1}", line=dict(color=colors[idx % 3], width=2.5)))

            cur = active_currency
            all_display_metrics.append({
                "פורטפוליו": f"פורטפוליו {idx + 1}",
                "💰 סכום התחלתי": format_currency(stats["start_val"] * exchange_rate, cur),
                "💰 סכום סופי": format_currency(stats["end_val"] * exchange_rate, cur),
                "💰 סה״כ הושקע": format_currency(stats["total_invested"] * exchange_rate, cur),
                "📤 סה״כ נמשך (ברוטו)": format_currency(stats["total_withdrawn_gross"] * exchange_rate, cur),
                "🏛️ סה״כ מס ששולם": format_currency(stats["total_tax_paid"] * exchange_rate, cur),
                "💸 סה״כ נמשך (נטו)": format_currency(stats["total_withdrawn_net"] * exchange_rate, cur),
                "📈 תשואה כוללת": f"{stats['total_return_pct']:.2f}%",
                "📈 תשואה שנתית (CAGR)": f"{stats['cagr']:.2f}%",
                "📉 תנודתיות שנתית": f"{stats['ann_vol']:.2f}%",
                "⚖️ שארפ": f"{stats['sharpe']:.2f}",
                "📉 ירידה מקסימלית": f"{stats['max_dd']:.2f}%",
                "🔄 שלב": pcfg["phase"],
            })
            all_stats_raw.append(stats)

        if any_data:
            # ── Chart ──
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### 📈 גרף השוואת פורטפוליו")
            fig.add_hline(y=initial_capital * exchange_rate, line_dash="dash", line_color="gray", annotation_text="סכום התחלתי", annotation_position="top left")
            if is_future:
                fig.add_vline(x=datetime.today().timestamp() * 1000, line_dash="dot", line_color="#ffcc00", annotation_text="היום", annotation_position="top right")
            fig.update_layout(template="plotly_dark", height=520, margin=dict(l=20, r=20, t=40, b=20), xaxis_title="תאריך", yaxis_title=f"שווי ({cur_symbol})", hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # ── Summary cards ──
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("### 📊 תוצאות")
            summary_cols = st.columns(num_p)
            for i, metrics in enumerate(all_display_metrics):
                with summary_cols[i]:
                    st.markdown(f'<div class="result-card"><b>פורטפוליו {i + 1}</b></div>', unsafe_allow_html=True)
                    st.metric("סכום התחלתי", metrics["💰 סכום התחלתי"])
                    st.metric("סכום סופי", metrics["💰 סכום סופי"])
                    st.metric("סה״כ הושקע (כולל הפקדות)", metrics["💰 סה״כ הושקע"])
                    st.metric("תשואה כוללת לתקופה", metrics["📈 תשואה כוללת"])
                    st.metric("תשואה שנתית ממוצעת (CAGR)", metrics["📈 תשואה שנתית (CAGR)"])
                    if metrics["📤 סה״כ נמשך (ברוטו)"] not in ("$0", "₪0"):
                        st.markdown("---")
                        st.markdown("**📤 פירוט משיכות ומיסוי:**")
                        st.metric("סה״כ נמשך (ברוטו)", metrics["📤 סה״כ נמשך (ברוטו)"])
                        st.metric(f"סה״כ מס רווחי הון ({capital_gains_tax_pct:.0f}%)", metrics["🏛️ סה״כ מס ששולם"])
                        st.metric("סה״כ נמשך (נטו ליד)", metrics["💸 סה״כ נמשך (נטו)"])

            with st.expander("📋 טבלת מדדים מלאה"):
                st.dataframe(pd.DataFrame(all_display_metrics).set_index("פורטפוליו"), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # ── Bottom-line comparison ──
            render_bottom_line_comparison(all_stats_raw, st.session_state.portfolios, num_p, exchange_rate, active_currency, CAPITAL_GAINS_TAX)

            # ── Recommendations ──
            render_recommendations(all_stats_raw, st.session_state.portfolios, initial_capital, global_monthly)
        else:
            st.error("לא נמצאו נתונים. ודא שבכל פורטפוליו יש נכסים תקינים.")

# ========================
# Footer
# ========================

st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#666; font-size:0.85rem; padding:0.5rem 0;'>"
    "📊 הנתונים מבוססים על מידע היסטורי בלבד ואינם מהווים המלצת השקעה. ביצועי העבר אינם מבטיחים תשואה עתידית."
    "</div>",
    unsafe_allow_html=True,
)
