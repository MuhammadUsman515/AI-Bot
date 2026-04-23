import json
import webbrowser
from pathlib import Path
from nova.utils.helpers import open_url


class WebMedia:

    def __init__(self, config):
        self.config = config

    # ── Tool Definitions ────────────────────────────────────────────────────

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "web_search",
                "description": "Search the web for any topic and return results",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "open_browser": {"type": "boolean", "description": "Open results in browser"},
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_weather",
                "description": "Get current weather and forecast for any location",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "City name or coordinates"},
                        "days": {"type": "integer", "description": "Forecast days (1-7)"},
                        "units": {
                            "type": "string",
                            "enum": ["metric", "imperial"],
                            "description": "Temperature units (metric=Celsius, imperial=Fahrenheit)"
                        },
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "get_news",
                "description": "Get latest news headlines by category",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["general", "technology", "business", "sports", "health", "science", "entertainment"],
                            "description": "News category"
                        },
                        "country": {"type": "string", "description": "Country code e.g. 'us', 'pk', 'gb'"},
                        "count": {"type": "integer", "description": "Number of headlines (default 5)"},
                    },
                    "required": []
                }
            },
            {
                "name": "play_media",
                "description": "Play music, video, or open YouTube in browser",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Song, video, or artist name"},
                        "media_type": {
                            "type": "string",
                            "enum": ["music", "video", "youtube"],
                            "description": "Type of media to play"
                        },
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_joke",
                "description": "Get a random joke",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["any", "programming", "dark", "pun", "misc"],
                            "description": "Joke category"
                        },
                    },
                    "required": []
                }
            },
            {
                "name": "get_quote",
                "description": "Get a daily inspirational or motivational quote",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Quote category e.g. 'motivational', 'wisdom', 'success'"
                        },
                    },
                    "required": []
                }
            },
            {
                "name": "get_stock_price",
                "description": "Get current stock price and market data",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Stock ticker symbol e.g. AAPL, GOOGL, TSLA"},
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_crypto_price",
                "description": "Get current cryptocurrency price",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "coin": {"type": "string", "description": "Crypto name or symbol e.g. bitcoin, ethereum, BTC"},
                        "currency": {"type": "string", "description": "Fiat currency to compare (default: usd)"},
                    },
                    "required": ["coin"]
                }
            },
            {
                "name": "get_sports_scores",
                "description": "Get live sports scores and match results",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sport": {"type": "string", "description": "Sport name: football, cricket, basketball, tennis"},
                        "team": {"type": "string", "description": "Team name (optional)"},
                    },
                    "required": ["sport"]
                }
            },
            {
                "name": "get_movie_info",
                "description": "Get movie or TV show information, ratings, cast",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Movie or TV show title"},
                        "year": {"type": "integer", "description": "Release year (optional)"},
                    },
                    "required": ["title"]
                }
            },
            {
                "name": "find_recipe",
                "description": "Find cooking recipes for any dish",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "dish": {"type": "string", "description": "Dish name to find recipe for"},
                        "dietary": {"type": "string", "description": "Dietary restrictions e.g. vegetarian, vegan, gluten-free"},
                    },
                    "required": ["dish"]
                }
            },
            {
                "name": "get_wikipedia",
                "description": "Search Wikipedia for information on any topic",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Topic to search on Wikipedia"},
                        "sentences": {"type": "integer", "description": "Number of sentences to return (default 5)"},
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_maps_route",
                "description": "Get directions or open maps for a location",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "destination": {"type": "string", "description": "Destination address or place name"},
                        "origin": {"type": "string", "description": "Starting point (optional)"},
                        "mode": {
                            "type": "string",
                            "enum": ["driving", "walking", "transit", "cycling"],
                            "description": "Travel mode"
                        },
                    },
                    "required": ["destination"]
                }
            },
            {
                "name": "get_workout_plan",
                "description": "Generate a workout or exercise plan",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "goal": {"type": "string", "description": "Fitness goal: weight_loss, muscle_gain, cardio, flexibility"},
                        "level": {
                            "type": "string",
                            "enum": ["beginner", "intermediate", "advanced"],
                            "description": "Fitness level"
                        },
                        "days_per_week": {"type": "integer", "description": "Days per week (1-7)"},
                    },
                    "required": ["goal"]
                }
            },
            {
                "name": "get_flight_info",
                "description": "Search for flight information or open flight search",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "from_city": {"type": "string", "description": "Departure city or airport code"},
                        "to_city": {"type": "string", "description": "Destination city or airport code"},
                        "date": {"type": "string", "description": "Travel date (YYYY-MM-DD)"},
                    },
                    "required": ["from_city", "to_city"]
                }
            },
            {
                "name": "track_package",
                "description": "Track a shipping package",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "tracking_number": {"type": "string", "description": "Package tracking number"},
                        "carrier": {"type": "string", "description": "Carrier name: fedex, ups, dhl, usps"},
                    },
                    "required": ["tracking_number"]
                }
            },
        ]

    def get_tool_handlers(self) -> dict:
        return {
            "web_search": self.web_search,
            "get_weather": self.get_weather,
            "get_news": self.get_news,
            "play_media": self.play_media,
            "get_joke": self.get_joke,
            "get_quote": self.get_quote,
            "get_stock_price": self.get_stock_price,
            "get_crypto_price": self.get_crypto_price,
            "get_sports_scores": self.get_sports_scores,
            "get_movie_info": self.get_movie_info,
            "find_recipe": self.find_recipe,
            "get_wikipedia": self.get_wikipedia,
            "get_maps_route": self.get_maps_route,
            "get_workout_plan": self.get_workout_plan,
            "get_flight_info": self.get_flight_info,
            "track_package": self.track_package,
        }

    # ── Implementations ──────────────────────────────────────────────────────

    def web_search(self, query: str, open_browser: bool = False) -> str:
        try:
            import requests
            encoded = query.replace(" ", "+")
            if open_browser:
                url = f"https://www.google.com/search?q={encoded}"
                webbrowser.open(url)
                return f"Opened Google search for: {query}"

            url = f"https://ddg-webapp-aagd.vercel.app/search?q={encoded}&kl=en-us"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                results = resp.json().get("results", [])[:5]
                lines = [f"Search results for: {query}"]
                for r in results:
                    lines.append(f"\n• {r.get('title', '')}\n  {r.get('href', '')}\n  {r.get('body', '')[:120]}...")
                return "\n".join(lines)

            url = f"https://www.google.com/search?q={encoded}"
            webbrowser.open(url)
            return f"Opened browser search for: {query}"
        except Exception as e:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(url)
            return f"Opened search in browser for: {query}"

    def get_weather(self, location: str, days: int = 1, units: str = "metric") -> str:
        api_key = self.config.openweather_api_key
        unit_symbol = "°C" if units == "metric" else "°F"
        try:
            import requests
            if not api_key:
                url = f"https://wttr.in/{location.replace(' ', '+')}?format=3"
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    return f"Weather in {location}: {resp.text.strip()}"
                webbrowser.open(f"https://wttr.in/{location}")
                return f"Opened weather for {location} in browser"

            url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units={units}"
            resp = requests.get(url, timeout=10)
            data = resp.json()

            if resp.status_code != 200:
                return f"Weather error: {data.get('message', 'Unknown error')}"

            main = data["main"]
            weather = data["weather"][0]
            wind = data.get("wind", {})
            result = [
                f"Weather in {data['name']}, {data.get('sys', {}).get('country', '')}:",
                f"  Condition: {weather['description'].capitalize()}",
                f"  Temperature: {main['temp']:.1f}{unit_symbol} (feels like {main['feels_like']:.1f}{unit_symbol})",
                f"  Min/Max: {main['temp_min']:.1f} / {main['temp_max']:.1f}{unit_symbol}",
                f"  Humidity: {main['humidity']}%",
                f"  Wind: {wind.get('speed', 0):.1f} m/s",
            ]
            return "\n".join(result)
        except Exception as e:
            try:
                import requests
                url = f"https://wttr.in/{location.replace(' ', '+')}?format=3"
                resp = requests.get(url, timeout=10)
                return f"Weather in {location}: {resp.text.strip()}"
            except Exception:
                return f"Weather unavailable: {e}"

    def get_news(self, category: str = "general", country: str = "us", count: int = 5) -> str:
        api_key = self.config.news_api_key
        try:
            import requests
            if not api_key:
                url = f"https://news.google.com/rss/headlines/section/topic/{category.upper()}?hl=en"
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    from xml.etree import ElementTree
                    root = ElementTree.fromstring(resp.content)
                    items = root.findall(".//item")[:count]
                    lines = [f"Top {category} news:"]
                    for item in items:
                        title = item.findtext("title", "")
                        lines.append(f"• {title}")
                    return "\n".join(lines)
                webbrowser.open("https://news.google.com")
                return "Opened Google News in browser"

            url = f"https://newsapi.org/v2/top-headlines?category={category}&country={country}&pageSize={count}&apiKey={api_key}"
            resp = requests.get(url, timeout=10)
            data = resp.json()

            if data.get("status") != "ok":
                return f"News error: {data.get('message')}"

            articles = data.get("articles", [])
            lines = [f"Top {category} headlines:"]
            for i, article in enumerate(articles, 1):
                lines.append(f"\n{i}. {article['title']}")
                lines.append(f"   Source: {article['source']['name']}")
                if article.get("description"):
                    lines.append(f"   {article['description'][:100]}...")
            return "\n".join(lines)
        except Exception as e:
            webbrowser.open("https://news.google.com")
            return f"Opened news in browser (API error: {e})"

    def play_media(self, query: str, media_type: str = "youtube") -> str:
        try:
            encoded = query.replace(" ", "+")
            if media_type in ("youtube", "video"):
                url = f"https://www.youtube.com/results?search_query={encoded}"
                webbrowser.open(url)
                return f"Opened YouTube search for: {query}"
            elif media_type == "music":
                url = f"https://open.spotify.com/search/{encoded}"
                webbrowser.open(url)
                return f"Opened Spotify search for: {query}"
        except Exception as e:
            return f"Media error: {e}"

    def get_joke(self, category: str = "any") -> str:
        try:
            import requests
            if category == "any":
                url = "https://v2.jokeapi.dev/joke/Any?safe-mode"
            elif category == "programming":
                url = "https://v2.jokeapi.dev/joke/Programming?safe-mode"
            elif category == "pun":
                url = "https://v2.jokeapi.dev/joke/Pun?safe-mode"
            else:
                url = "https://v2.jokeapi.dev/joke/Any?safe-mode"

            resp = requests.get(url, timeout=10)
            data = resp.json()

            if data.get("type") == "single":
                return f"😄 {data['joke']}"
            elif data.get("type") == "twopart":
                return f"😄 {data['setup']}\n\n😂 {data['delivery']}"
        except Exception as e:
            jokes = [
                "Why do programmers prefer dark mode? Because light attracts bugs!",
                "Why did the computer keep freezing? Because it left its Windows open!",
                "I told my computer I needed a break. Now it won't stop sending me Kit-Kat ads.",
                "Why was the math book sad? Because it had too many problems.",
                "What do you call a computer that sings? A Dell.",
            ]
            import random
            return f"😄 {random.choice(jokes)}"

    def get_quote(self, category: str = "motivational") -> str:
        try:
            import requests
            resp = requests.get("https://zenquotes.io/api/random", timeout=10)
            data = resp.json()
            if data:
                q = data[0]
                return f'"{q.get("q", "")}" — {q.get("a", "Unknown")}'
        except Exception:
            pass
        quotes = [
            '"The only way to do great work is to love what you do." — Steve Jobs',
            '"Innovation distinguishes between a leader and a follower." — Steve Jobs',
            '"The future belongs to those who believe in the beauty of their dreams." — Eleanor Roosevelt',
            '"Success is not final, failure is not fatal: it is the courage to continue that counts." — Winston Churchill',
            '"In the middle of every difficulty lies opportunity." — Albert Einstein',
        ]
        import random
        return random.choice(quotes)

    def get_stock_price(self, symbol: str) -> str:
        try:
            import requests
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol.upper()}?interval=1d&range=1d"
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            data = resp.json()

            result = data.get("chart", {}).get("result", [])
            if not result:
                return f"Stock symbol not found: {symbol}"

            meta = result[0].get("meta", {})
            price = meta.get("regularMarketPrice", "N/A")
            prev_close = meta.get("previousClose", "N/A")
            change = (price - prev_close) if isinstance(price, (int, float)) and isinstance(prev_close, (int, float)) else 0
            change_pct = (change / prev_close * 100) if prev_close else 0
            currency = meta.get("currency", "USD")
            arrow = "↑" if change >= 0 else "↓"

            return (
                f"📈 {symbol.upper()} Stock Price\n"
                f"  Current: {price} {currency}\n"
                f"  Change: {arrow} {change:.2f} ({change_pct:.2f}%)\n"
                f"  Previous Close: {prev_close} {currency}\n"
                f"  Market: {meta.get('exchangeName', 'N/A')}"
            )
        except Exception as e:
            webbrowser.open(f"https://finance.yahoo.com/quote/{symbol}")
            return f"Opened Yahoo Finance for {symbol} (API error: {e})"

    def get_crypto_price(self, coin: str, currency: str = "usd") -> str:
        try:
            import requests
            coin_id = coin.lower().replace(" ", "-")
            coin_map = {
                "btc": "bitcoin", "eth": "ethereum", "bnb": "binancecoin",
                "xrp": "ripple", "ada": "cardano", "sol": "solana",
                "doge": "dogecoin", "dot": "polkadot", "avax": "avalanche-2",
                "matic": "matic-network", "link": "chainlink",
            }
            coin_id = coin_map.get(coin_id, coin_id)
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={currency}&include_24hr_change=true&include_market_cap=true"
            resp = requests.get(url, timeout=10)
            data = resp.json()

            if coin_id not in data:
                return f"Crypto not found: {coin}"

            price_data = data[coin_id]
            price = price_data.get(currency, "N/A")
            change = price_data.get(f"{currency}_24h_change", 0)
            market_cap = price_data.get(f"{currency}_market_cap", 0)
            arrow = "↑" if change >= 0 else "↓"

            return (
                f"🪙 {coin.upper()} Price\n"
                f"  Price: {price:,.4f} {currency.upper()}\n"
                f"  24h Change: {arrow} {change:.2f}%\n"
                f"  Market Cap: ${market_cap:,.0f}"
            )
        except Exception as e:
            webbrowser.open(f"https://www.coingecko.com/en/coins/{coin.lower()}")
            return f"Opened CoinGecko for {coin} (API error: {e})"

    def get_sports_scores(self, sport: str, team: str = None) -> str:
        try:
            import requests
            queries = {
                "football": "football scores today",
                "soccer": "football scores today",
                "cricket": "cricket scores today",
                "basketball": "basketball scores today",
                "tennis": "tennis scores today",
            }
            query = queries.get(sport.lower(), f"{sport} scores today")
            if team:
                query = f"{team} {sport} score"

            encoded = query.replace(" ", "+")
            webbrowser.open(f"https://www.google.com/search?q={encoded}")
            return f"Opened {sport} scores for{' ' + team if team else ''} in browser"
        except Exception as e:
            return f"Sports scores error: {e}"

    def get_movie_info(self, title: str, year: int = None) -> str:
        try:
            import requests
            search_term = title + (f" {year}" if year else "")
            url = f"https://www.omdbapi.com/?t={title.replace(' ', '+')}&apikey=trilogy"
            if year:
                url += f"&y={year}"
            resp = requests.get(url, timeout=10)
            data = resp.json()

            if data.get("Response") == "True":
                return (
                    f"🎬 {data.get('Title')} ({data.get('Year')})\n"
                    f"  Genre: {data.get('Genre')}\n"
                    f"  Director: {data.get('Director')}\n"
                    f"  Cast: {data.get('Actors')}\n"
                    f"  Rating: {data.get('imdbRating')}/10 ({data.get('imdbVotes')} votes)\n"
                    f"  Plot: {data.get('Plot')}\n"
                    f"  Runtime: {data.get('Runtime')}"
                )
            else:
                encoded = search_term.replace(" ", "+")
                webbrowser.open(f"https://www.imdb.com/find?q={encoded}")
                return f"Opened IMDB search for: {title}"
        except Exception as e:
            webbrowser.open(f"https://www.imdb.com/find?q={title.replace(' ', '+')}")
            return f"Opened IMDB for: {title}"

    def find_recipe(self, dish: str, dietary: str = None) -> str:
        try:
            import requests
            query = dish
            if dietary:
                query = f"{dietary} {dish}"
            encoded = query.replace(" ", "+")
            url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={dish.replace(' ', '+')}"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            meals = data.get("meals")

            if meals:
                meal = meals[0]
                ingredients = []
                for i in range(1, 21):
                    ingredient = meal.get(f"strIngredient{i}", "").strip()
                    measure = meal.get(f"strMeasure{i}", "").strip()
                    if ingredient:
                        ingredients.append(f"  • {measure} {ingredient}".strip())

                return (
                    f"🍳 {meal.get('strMeal')}\n"
                    f"Category: {meal.get('strCategory')} | Cuisine: {meal.get('strArea')}\n\n"
                    f"Ingredients:\n" + "\n".join(ingredients[:15]) + "\n\n"
                    f"Instructions:\n{meal.get('strInstructions', '')[:500]}...\n"
                    f"(Full recipe: {meal.get('strSource', meal.get('strYoutube', 'N/A'))})"
                )
            else:
                webbrowser.open(f"https://www.allrecipes.com/search?q={encoded}")
                return f"Opened AllRecipes search for: {dish}"
        except Exception as e:
            webbrowser.open(f"https://www.allrecipes.com/search?q={dish.replace(' ', '+')}")
            return f"Opened recipe search for: {dish}"

    def get_wikipedia(self, query: str, sentences: int = 5) -> str:
        try:
            import wikipedia
            results = wikipedia.search(query)
            if not results:
                return f"No Wikipedia results for: {query}"
            page = wikipedia.page(results[0])
            summary = wikipedia.summary(results[0], sentences=sentences)
            return f"📚 {page.title}\n\n{summary}\n\nFull article: {page.url}"
        except ImportError:
            try:
                import requests
                url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
                resp = requests.get(url, timeout=10)
                data = resp.json()
                if data.get("extract"):
                    return f"📚 {data['title']}\n\n{data['extract'][:500]}"
            except Exception:
                pass
            webbrowser.open(f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}")
            return f"Opened Wikipedia for: {query}"
        except Exception as e:
            webbrowser.open(f"https://en.wikipedia.org/wiki/Special:Search?search={query}")
            return f"Opened Wikipedia search for: {query} (error: {e})"

    def get_maps_route(self, destination: str, origin: str = None, mode: str = "driving") -> str:
        try:
            mode_map = {"driving": "driving", "walking": "walking", "transit": "transit", "cycling": "bicycling"}
            gmode = mode_map.get(mode, "driving")
            if origin:
                url = f"https://www.google.com/maps/dir/{origin.replace(' ', '+')}/ {destination.replace(' ', '+')}/?travelmode={gmode}"
            else:
                url = f"https://www.google.com/maps/search/{destination.replace(' ', '+')}"
            webbrowser.open(url)
            return f"Opened Google Maps directions to: {destination}"
        except Exception as e:
            return f"Maps error: {e}"

    def get_workout_plan(self, goal: str, level: str = "beginner", days_per_week: int = 3) -> str:
        plans = {
            "weight_loss": {
                "beginner": [
                    "Day 1: 30 min brisk walk + 20 min yoga",
                    "Day 2: Rest or light stretching",
                    "Day 3: 20 min jog + 15 min bodyweight squats & lunges",
                    "Day 4: Rest",
                    "Day 5: 30 min cycling + core exercises (planks, crunches)",
                    "Day 6: 20 min swim or cardio of choice",
                    "Day 7: Rest",
                ],
                "intermediate": [
                    "Day 1: HIIT 30 min + 15 min abs",
                    "Day 2: Weight training (upper body)",
                    "Day 3: 45 min run or cycling",
                    "Day 4: Weight training (lower body)",
                    "Day 5: HIIT 30 min",
                    "Day 6: Active recovery (yoga or swim)",
                    "Day 7: Rest",
                ],
            },
            "muscle_gain": {
                "beginner": [
                    "Day 1: Push (chest, triceps, shoulders) – 3x10 bench, push-ups, shoulder press",
                    "Day 2: Rest",
                    "Day 3: Pull (back, biceps) – 3x10 rows, pull-ups, curls",
                    "Day 4: Rest",
                    "Day 5: Legs – 3x10 squats, lunges, calf raises",
                    "Day 6-7: Rest",
                ],
                "intermediate": [
                    "Day 1: Chest + Triceps (bench press, dips, cable pushdown)",
                    "Day 2: Back + Biceps (deadlifts, pull-ups, curls)",
                    "Day 3: Shoulders + Abs",
                    "Day 4: Legs (squats, leg press, hamstring curl)",
                    "Day 5: Arms + Core",
                    "Day 6-7: Rest",
                ],
            },
            "cardio": {
                "beginner": [
                    "Day 1: 20 min walk",
                    "Day 2: Rest",
                    "Day 3: 15 min jog",
                    "Day 4: Rest",
                    "Day 5: 25 min cycling",
                    "Day 6-7: Rest",
                ],
            },
        }

        goal_key = goal.lower().replace(" ", "_")
        plan = plans.get(goal_key, {}).get(level, plans.get("cardio", {}).get("beginner", []))

        tip_map = {
            "weight_loss": "Stay hydrated, maintain caloric deficit, get 7-8 hours of sleep.",
            "muscle_gain": "Eat in caloric surplus with high protein (0.8-1g per lb bodyweight).",
            "cardio": "Gradually increase duration/intensity each week.",
        }

        result = [
            f"💪 {goal.replace('_', ' ').title()} Workout Plan",
            f"Level: {level.capitalize()} | {days_per_week} days/week",
            "",
            "Weekly Schedule:",
        ]
        for day in plan[:days_per_week + 1]:
            result.append(f"  • {day}")

        result.append(f"\nTip: {tip_map.get(goal_key, 'Consistency is key!')}")
        return "\n".join(result)

    def get_flight_info(self, from_city: str, to_city: str, date: str = None) -> str:
        try:
            query = f"flights from {from_city} to {to_city}"
            if date:
                query += f" on {date}"
            encoded = query.replace(" ", "+")
            webbrowser.open(f"https://www.google.com/travel/flights?q={encoded}")
            return f"Opened Google Flights: {from_city} → {to_city}" + (f" on {date}" if date else "")
        except Exception as e:
            return f"Flight search error: {e}"

    def track_package(self, tracking_number: str, carrier: str = None) -> str:
        try:
            carrier_urls = {
                "fedex": f"https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
                "ups": f"https://www.ups.com/track?tracknum={tracking_number}",
                "dhl": f"https://www.dhl.com/en/express/tracking.html?AWB={tracking_number}",
                "usps": f"https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}",
            }
            if carrier and carrier.lower() in carrier_urls:
                url = carrier_urls[carrier.lower()]
            else:
                url = f"https://www.google.com/search?q=track+package+{tracking_number}"
            webbrowser.open(url)
            return f"Opened package tracker for: {tracking_number}"
        except Exception as e:
            return f"Tracking error: {e}"
