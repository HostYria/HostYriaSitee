#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lodoxa Telegram Bot - Arabic Electronic Charging Services
A comprehensive bot for managing electronic charging services with admin controls
"""

import os
import json
import logging
import asyncio
import string
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from uuid import uuid4

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, filters

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8397835580:AAGV35UkJSqqsZ0eV1ZpJxHsCSlWgasDE8M")

# Admin user ID
ADMIN_ID = 8319511583

# Special admin for bot branding (ADMG01C)
ADMG01C = 0000000000

# Required channel
CHANNEL_USERNAME = "@SyriaCashStore"

# Orders channel - يمكنك تغيير هذا إلى معرف القناة أو اسم المستخدم للقناة المطلوبة
ORDERS_CHANNEL = "-1003251898613"  # ضع هنا اسم القناة العامة أو معرف القناة مثل -1001234567890

# Channel for balance recharge requests - قناة طلبات شحن الرصيد
BALANCE_REQUESTS_CHANNEL = "-1003290201533"

# Channel for new user notifications - قناة إشعارات المستخدمين الجدد
NEW_USER_CHANNEL = "-1003292544444"

# Conversation states
(MAIN_MENU, SELECTING_SERVICE, SELECTING_APP_GAME, SELECTING_CATEGORY,
 ENTERING_QUANTITY, ENTERING_ACCOUNT_ID, CONFIRMING_ORDER,
 ADMIN_PANEL, MANAGING_APPS, ADDING_APP, EDITING_APP, ADDING_CATEGORY,
 SUPPORT_MESSAGE, ADD_BALANCE, SELECTING_APP_TYPE, ENTERING_APP_NAME,
 MANAGING_CATEGORIES, SELECTING_CATEGORY_SERVICE, SELECTING_CATEGORY_APP,
 SELECTING_CATEGORY_TYPE, ENTERING_FIXED_CATEGORIES, ENTERING_QUANTITY_CATEGORY_NAME,
 ENTERING_MIN_ORDER, ENTERING_MAX_ORDER, ENTERING_PRICE_PER_UNIT,
 SELECTING_DELETE_ACTION, SELECTING_DELETE_SERVICE_TYPE, SELECTING_DELETE_ITEM,
 CONFIRMING_DELETE, SELECTING_DELETE_CATEGORY_SERVICE, SELECTING_DELETE_CATEGORY_APP,
 SELECTING_DELETE_CATEGORY, CONFIRMING_DELETE_CATEGORY, SETTING_SUPPORT_USERNAME,
 SELECTING_PAYMENT_METHOD, ENTERING_CHARGE_CODE, ENTERING_SYRIATEL_AMOUNT,
 CONFIRMING_SYRIATEL_PAYMENT, ENTERING_SYRIATEL_TRANSACTION, MANAGING_PAYMENT_ADDRESSES,
 SETTING_SYRIATEL_ADDRESS, SETTING_SHAMCASH_ADDRESS, MANAGING_CHARGE_CODES,
 ENTERING_CHARGE_CODE_VALUE, CONFIRMING_CHARGE_CODE_GENERATION, MANAGING_PAYMENTS,
 ENTERING_PAYMENT_NAME, ENTERING_PAYMENT_PRICE,
 CONFIRMING_PAYMENT_ADD, SELECTING_PAYMENT_TO_DELETE, CONFIRMING_PAYMENT_DELETE,
 ENTERING_BROADCAST_MESSAGE, CONFIRMING_BROADCAST, BOT_SETTINGS,
 MANAGING_PAYMENT_SERVICES, ENTERING_SERVICE_NAME,
 ADDING_SERVICE_CATEGORIES, ENTERING_CATEGORY_NAME, ENTERING_CATEGORY_PRICE,
 SELECTING_CATEGORY_INPUT_TYPE, CONFIRMING_CATEGORY_ADD, SELECTING_SERVICE_TO_EDIT,
 ENTERING_PAYMENT_INPUT_DATA, CONFIRMING_PAYMENT_SERVICE_ORDER, SELECTING_CATEGORY_TO_DELETE, CONFIRMING_CATEGORY_DELETE,
 SELECTING_CATEGORY_TO_EDIT, EDITING_CATEGORY_PRICE, CONFIRMING_CATEGORY_EDIT,
 USER_MANAGEMENT, VIEWING_STATISTICS, ENTERING_USER_ID_FOR_ACTION, SELECTING_USER_ACTION,
 CONFIRMING_USER_ACTION, ENTERING_FREEZE_DURATION, ENTERING_BALANCE_AMOUNT,
 ENTERING_PRIVATE_MESSAGE_USER_ID, ENTERING_PRIVATE_MESSAGE_TEXT, CONFIRMING_PRIVATE_MESSAGE,
 MANAGING_AGENTS, ENTERING_AGENT_NAME, ENTERING_AGENT_USER_ID, ENTERING_AGENT_COMMISSION,
 CONFIRMING_AGENT_ADD, SELECTING_AGENT_TO_EDIT, EDITING_AGENT_COMMISSION, CONFIRMING_AGENT_EDIT,
 SELECTING_AGENT_TO_DELETE, CONFIRMING_AGENT_DELETE, VIEWING_AGENT_STATISTICS,
 AGENT_PANEL, CONFIRMING_WITHDRAWAL_REQUEST, SETTING_WITHDRAWAL_FEES, BULK_PRICE_ADJUSTMENT, SELECTING_ADJUSTMENT_TYPE,
 ENTERING_ADJUSTMENT_VALUE, CONFIRMING_BULK_ADJUSTMENT,
 MANAGING_ORDERS_CHANNEL, SETTING_PAYEER_DATA, SETTING_USDT_DATA, ENTERING_PAYEER_USD_AMOUNT,
 ADMG01C_PANEL, ENTERING_NEW_BOT_NAME, CONFIRMING_BOT_NAME_CHANGE,
 MANAGING_ADMINS_ADMG01C, ADDING_ADMIN_ADMG01C, ENTERING_ADMIN_USER_ID_ADMG01C,
 CONFIRMING_ADMIN_ADD_ADMG01C, SELECTING_ADMIN_TO_DELETE_ADMG01C, CONFIRMING_ADMIN_DELETE_ADMG01C,
 MANAGING_ADMINS, ADDING_ADMIN, ENTERING_ADMIN_USER_ID, CONFIRMING_ADMIN_ADD,
 SELECTING_ADMIN_TO_DELETE, CONFIRMING_ADMIN_DELETE, SELECTING_SHAMCASH_CURRENCY,
 MANAGING_REFERRALS, ENTERING_REFERRAL_USER_ID, EDITING_USER_REFERRAL_DATA,
 ENTERING_NEW_REFERRAL_COUNT, ENTERING_NEW_REFERRAL_EARNINGS, ENTERING_REFERRAL_RATES,
 VIEWING_TOP_REFERRERS, VIEWING_REFERRAL_TRANSACTIONS) = range(125)

def generate_order_id():
    """Generate a unique 10-character order ID with letters and numbers"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=10))

class DataManager:
    """Handles all data operations with JSON files"""

    def __init__(self):
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)
        self.users_file = os.path.join(self.data_dir, "users.json")
        self.apps_file = os.path.join(self.data_dir, "apps.json")
        self.games_file = os.path.join(self.data_dir, "games.json")
        self.orders_file = os.path.join(self.data_dir, "orders.json")
        self.settings_file = os.path.join(self.data_dir, "settings.json")
        self.referral_logs_file = os.path.join(self.data_dir, "referral_logs.json")
        self._init_files()

    def _init_files(self):
        """Initialize JSON files if they don't exist"""
        try:
            if not os.path.exists(self.users_file):
                logger.info(f"Creating users file: {self.users_file}")
                self._save_json(self.users_file, {})

            if not os.path.exists(self.apps_file):
                logger.info(f"Creating apps file: {self.apps_file}")
                # Initialize with empty apps data
                apps_data = {}
                self._save_json(self.apps_file, apps_data)

            if not os.path.exists(self.games_file):
                logger.info(f"Creating games file: {self.games_file}")
                # Initialize with empty games data
                games_data = {}
                self._save_json(self.games_file, games_data)

            if not os.path.exists(self.orders_file):
                logger.info(f"Creating orders file: {self.orders_file}")
                self._save_json(self.orders_file, {})

            if not os.path.exists(self.settings_file):
                logger.info(f"Creating settings file: {self.settings_file}")
                self._save_json(self.settings_file, {
                    "support_username": None,
                    "syriatel_address": "0000",
                    "shamcash_address": "0000",
                    "bot_enabled": True,
                    "charge_codes": {},
                    "payment_services": {},
                    "agents": {},
                    "withdrawal_fees": 0,
                    "bot_name": "لودوكسا",
                    "bot_name_english": "Lodoxa",
                    "referral_enabled": True,
                    "referral_level_1_percentage": 1.0,
                    "referral_level_2_percentage": 0.5,
                    "next_referral_id": 500,
                    "show_referral_button": True
                })

            if not os.path.exists(self.referral_logs_file):
                logger.info(f"Creating referral logs file: {self.referral_logs_file}")
                self._save_json(self.referral_logs_file, {})

            logger.info("All data files initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing data files: {e}")
            raise

    def _load_json(self, filepath: str) -> Dict:
        """Load JSON data from file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"Successfully loaded data from {filepath}")
                return data
        except FileNotFoundError:
            logger.warning(f"File not found: {filepath}, returning empty dict")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {filepath}: {e}")
            # Create backup of corrupted file
            backup_path = f"{filepath}.backup"
            try:
                os.rename(filepath, backup_path)
                logger.info(f"Corrupted file backed up to {backup_path}")
            except:
                pass
            return {}
        except Exception as e:
            logger.error(f"Unexpected error loading {filepath}: {e}")
            return {}

    def _save_json(self, filepath: str, data: Dict):
        """Save data to JSON file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Write to temporary file first
            temp_filepath = f"{filepath}.tmp"
            with open(temp_filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # Atomic move to final location
            os.replace(temp_filepath, filepath)
            logger.debug(f"Successfully saved data to {filepath}")

        except Exception as e:
            logger.error(f"Error saving data to {filepath}: {e}")
            # Clean up temp file if it exists
            temp_filepath = f"{filepath}.tmp"
            if os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except:
                    pass
            raise

    def get_user(self, user_id: int) -> Dict:
        """Get user data"""
        users = self._load_json(self.users_file)
        if str(user_id) not in users:
            settings = self._load_json(self.settings_file)
            next_id = settings.get("next_referral_id", 500)
            settings["next_referral_id"] = next_id + 1
            self._save_json(self.settings_file, settings)

            users[str(user_id)] = {
                "balance": 0,
                "created_at": datetime.now().isoformat(),
                "orders": [],
                "referral_id": next_id,
                "referred_by": None,
                "referrals_level_1": [],
                "referrals_level_2": [],
                "referral_earnings": 0,
                "total_referral_earnings": 0,
                "has_purchased": False
            }
            self._save_json(self.users_file, users)
        return users[str(user_id)]

    def update_user_balance(self, user_id: int, amount: int):
        """Update user balance"""
        users = self._load_json(self.users_file)
        if str(user_id) not in users:
            self.get_user(user_id)  # Create user if doesn't exist
            users = self._load_json(self.users_file)

        users[str(user_id)]["balance"] += amount
        self._save_json(self.users_file, users)

    def get_apps(self) -> Dict:
        """Get all apps"""
        return self._load_json(self.apps_file)

    def get_games(self) -> Dict:
        """Get all games"""
        return self._load_json(self.games_file)

    def save_order(self, order_data: Dict) -> str:
        """Save new order and return order ID"""
        orders = self._load_json(self.orders_file)
        order_id = order_data["order_id"]
        orders[order_id] = order_data
        self._save_json(self.orders_file, orders)
        return order_id

    def update_order_status(self, order_id: str, status: str):
        """Update order status"""
        orders = self._load_json(self.orders_file)
        if order_id in orders:
            orders[order_id]["status"] = status
            self._save_json(self.orders_file, orders)

    def get_pending_orders(self) -> Dict:
        """Get all pending orders"""
        orders = self._load_json(self.orders_file)
        return {k: v for k, v in orders.items() if v.get("status") == "قيد المعالجة"}

    def add_app_or_game(self, app_id: str, name: str, service_type: str):
        """Add new app or game"""
        if service_type == 'app':
            apps = self._load_json(self.apps_file)
            apps[app_id] = {
                "name": name,
                "type": "app",
                "categories": {}
            }
            self._save_json(self.apps_file, apps)
        else:
            games = self._load_json(self.games_file)
            games[app_id] = {
                "name": name,
                "type": "game",
                "categories": {}
            }
            self._save_json(self.games_file, games)

    def add_category(self, service_type: str, app_id: str, category_id: str, category_data: Dict):
        """Add category to app or game"""
        if service_type == 'app':
            apps = self._load_json(self.apps_file)
            if app_id in apps:
                apps[app_id]["categories"][category_id] = category_data
                self._save_json(self.apps_file, apps)
        else:
            games = self._load_json(self.games_file)
            if app_id in games:
                games[app_id]["categories"][category_id] = category_data
                self._save_json(self.games_file, games)

    def delete_app_or_game(self, service_type: str, app_id: str):
        """Delete app or game completely"""
        if service_type == 'app':
            apps = self._load_json(self.apps_file)
            if app_id in apps:
                del apps[app_id]
                self._save_json(self.apps_file, apps)
                return True
        else:
            games = self._load_json(self.games_file)
            if app_id in games:
                del games[app_id]
                self._save_json(self.games_file, games)
                return True
        return False

    def delete_category(self, service_type: str, app_id: str, category_id: str):
        """Delete category from app or game"""
        if service_type == 'app':
            apps = self._load_json(self.apps_file)
            if app_id in apps and category_id in apps[app_id]["categories"]:
                del apps[app_id]["categories"][category_id]
                self._save_json(self.apps_file, apps)
                return True
        else:
            games = self._load_json(self.games_file)
            if app_id in games and category_id in games[app_id]["categories"]:
                del games[app_id]["categories"][category_id]
                self._save_json(self.games_file, games)
                return True
        return False

    def get_support_username(self) -> Optional[str]:
        """Get support username"""
        settings = self._load_json(self.settings_file)
        return settings.get("support_username")

    def set_support_username(self, username: str):
        """Set support username"""
        settings = self._load_json(self.settings_file)
        settings["support_username"] = username
        self._save_json(self.settings_file, settings)

    def get_syriatel_address(self) -> str:
        """Get Syriatel cash address"""
        settings = self._load_json(self.settings_file)
        return settings.get("syriatel_address", "0000")

    def set_syriatel_address(self, address: str):
        """Set Syriatel cash address"""
        settings = self._load_json(self.settings_file)
        settings["syriatel_address"] = address
        self._save_json(self.settings_file, settings)

    def get_shamcash_address(self) -> str:
        """Get Sham cash address - for backward compatibility"""
        settings = self._load_json(self.settings_file)
        shamcash_data = settings.get("shamcash_data")
        if shamcash_data:
            return shamcash_data.get("address", "0000")
        return settings.get("shamcash_address", "0000")

    def set_shamcash_address(self, address: str):
        """Set Sham cash address - for backward compatibility"""
        settings = self._load_json(self.settings_file)
        shamcash_data = settings.get("shamcash_data", {"address": "0000", "exchange_rate": 3000})
        shamcash_data["address"] = address
        settings["shamcash_data"] = shamcash_data
        self._save_json(self.settings_file, settings)

    def get_shamcash_data(self) -> Dict:
        """Get Sham Cash payment data"""
        settings = self._load_json(self.settings_file)
        shamcash_data = settings.get("shamcash_data")
        if shamcash_data:
            return shamcash_data
        old_address = settings.get("shamcash_address", "0000")
        return {"address": old_address, "exchange_rate": 3000}

    def set_shamcash_data(self, address: str, exchange_rate: int):
        """Set Sham Cash payment data"""
        settings = self._load_json(self.settings_file)
        settings["shamcash_data"] = {
            "address": address,
            "exchange_rate": exchange_rate
        }
        self._save_json(self.settings_file, settings)

    def get_payeer_data(self) -> Dict:
        """Get Payeer payment data"""
        settings = self._load_json(self.settings_file)
        return settings.get("payeer_data", {"address": "0000", "exchange_rate": 3000})

    def set_payeer_data(self, address: str, exchange_rate: int):
        """Set Payeer payment data"""
        settings = self._load_json(self.settings_file)
        settings["payeer_data"] = {
            "address": address,
            "exchange_rate": exchange_rate
        }
        self._save_json(self.settings_file, settings)

    def get_usdt_data(self) -> Dict:
        """Get USDT BEP-20 payment data"""
        settings = self._load_json(self.settings_file)
        return settings.get("usdt_data", {"address": "0000", "exchange_rate": 3000})

    def set_usdt_data(self, address: str, exchange_rate: int):
        """Set USDT BEP-20 payment data"""
        settings = self._load_json(self.settings_file)
        settings["usdt_data"] = {
            "address": address,
            "exchange_rate": exchange_rate
        }
        self._save_json(self.settings_file, settings)

    def save_charge_code(self, code: str, value: int) -> str:
        """Save charge code with its value"""
        settings = self._load_json(self.settings_file)
        if "charge_codes" not in settings:
            settings["charge_codes"] = {}

        settings["charge_codes"][code] = {
            "value": value,
            "used": False,
            "created_at": datetime.now().isoformat()
        }
        self._save_json(self.settings_file, settings)
        return code

    def get_charge_code_value(self, code: str) -> Optional[int]:
        """Get charge code value if valid and unused"""
        settings = self._load_json(self.settings_file)
        codes = settings.get("charge_codes", {})

        if code in codes and not codes[code]["used"]:
            return codes[code]["value"]
        return None

    def use_charge_code(self, code: str) -> bool:
        """Mark charge code as used"""
        settings = self._load_json(self.settings_file)
        codes = settings.get("charge_codes", {})

        if code in codes and not codes[code]["used"]:
            settings["charge_codes"][code]["used"] = True
            settings["charge_codes"][code]["used_at"] = datetime.now().isoformat()
            self._save_json(self.settings_file, settings)
            return True
        return False

    def get_all_charge_codes(self) -> Dict:
        """Get all charge codes with their status"""
        settings = self._load_json(self.settings_file)
        return settings.get("charge_codes", {})

    def is_bot_enabled(self) -> bool:
        """Check if bot is enabled"""
        settings = self._load_json(self.settings_file)
        return settings.get("bot_enabled", True)

    def set_bot_enabled(self, enabled: bool):
        """Set bot enabled status"""
        settings = self._load_json(self.settings_file)
        settings["bot_enabled"] = enabled
        self._save_json(self.settings_file, settings)

    def get_payments(self) -> Dict:
        """Get all payment services"""
        settings = self._load_json(self.settings_file)
        return settings.get("payment_services", {})

    def add_payment_service(self, service_id: str, name: str):
        """Add new payment service"""
        settings = self._load_json(self.settings_file)
        if "payment_services" not in settings:
            settings["payment_services"] = {}

        settings["payment_services"][service_id] = {
            "name": name,
            "type": "payment",
            "categories": {},
            "created_at": datetime.now().isoformat()
        }
        self._save_json(self.settings_file, settings)

    def add_payment_category(self, service_id: str, category_id: str, category_data: Dict):
        """Add category to payment service"""
        settings = self._load_json(self.settings_file)
        if "payment_services" not in settings:
            settings["payment_services"] = {}

        if service_id not in settings["payment_services"]:
            return False

        if "categories" not in settings["payment_services"][service_id]:
            settings["payment_services"][service_id]["categories"] = {}

        settings["payment_services"][service_id]["categories"][category_id] = category_data
        settings["payment_services"][service_id]["categories"][category_id]["created_at"] = datetime.now().isoformat()
        self._save_json(self.settings_file, settings)
        return True

    def delete_payment_service(self, service_id: str) -> bool:
        """Delete payment service"""
        settings = self._load_json(self.settings_file)
        payments = settings.get("payment_services", {})

        if service_id in payments:
            del settings["payment_services"][service_id]
            self._save_json(self.settings_file, settings)
            return True
        return False

    def delete_payment_category(self, service_id: str, category_id: str) -> bool:
        """Delete category from payment service"""
        settings = self._load_json(self.settings_file)
        payments = settings.get("payment_services", {})

        if service_id in payments and category_id in payments[service_id]["categories"]:
            del settings["payment_services"][service_id]["categories"][category_id]
            self._save_json(self.settings_file, settings)
            return True
        return False

    def get_all_users(self) -> Dict:
        """Get all users for broadcasting"""
        return self._load_json(self.users_file)

    def get_spending_last_15_days(self) -> int:
        """Calculate total user spending in the last 15 days"""
        orders = self._load_json(self.orders_file)
        cutoff_date = datetime.now() - timedelta(days=15)

        total_spending = 0
        for order in orders.values():
            try:
                # Parse order timestamp
                timestamp_str = order.get('timestamp', '')
                # Handle different timestamp formats
                if timestamp_str:
                    try:
                        order_date = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    except:
                        try:
                            order_date = datetime.fromisoformat(timestamp_str)
                        except:
                            continue

                    # Check if order is within last 15 days and completed
                    if order_date >= cutoff_date and order.get('status') in ['مكتمل وتم الشحن بنجاح', 'تم الموافقة', 'تم التنفيذ']:
                        total_spending += order.get('price', 0)
            except Exception as e:
                logger.debug(f"Error processing order for spending calculation: {e}")
                continue

        return total_spending

    def get_user_statistics(self) -> Dict:
        """Get comprehensive user statistics"""
        users = self._load_json(self.users_file)
        orders = self._load_json(self.orders_file)

        total_users = len(users)
        total_balance = sum(user_data.get('balance', 0) for user_data in users.values())

        # Get top 3 users by balance
        users_with_balance = [
            {
                'user_id': user_id,
                'balance': user_data.get('balance', 0),
                'username': user_data.get('username', f'User_{user_id}')
            }
            for user_id, user_data in users.items()
        ]

        top_3_users = sorted(users_with_balance, key=lambda x: x['balance'], reverse=True)[:3]

        # Count banned and frozen users
        banned_users = sum(1 for user_data in users.values() if user_data.get('is_banned', False))
        frozen_users = sum(1 for user_id in users.keys() if self.is_user_frozen(int(user_id)))

        # Financial statistics from orders
        total_orders = len(orders)
        completed_orders = [order for order in orders.values() if order.get('status') in ['مكتمل وتم الشحن بنجاح', 'تم الموافقة', 'تم التنفيذ']]
        pending_orders = [order for order in orders.values() if order.get('status') == 'قيد المعالجة']
        rejected_orders = [order for order in orders.values() if order.get('status') in ['مرفوض ولم تكتمل العملية', 'مرفوض']]

        # Calculate revenue (completed orders only)
        total_revenue = sum(order.get('price', 0) for order in completed_orders)
        pending_revenue = sum(order.get('price', 0) for order in pending_orders)

        # Average order value
        avg_order_value = total_revenue / len(completed_orders) if completed_orders else 0

        # Orders by service type
        app_orders = [order for order in completed_orders if order.get('service_type') == 'app']
        game_orders = [order for order in completed_orders if order.get('service_type') == 'game']
        payment_orders = [order for order in completed_orders if order.get('service_type') == 'payment_service']

        app_revenue = sum(order.get('price', 0) for order in app_orders)
        game_revenue = sum(order.get('price', 0) for order in game_orders)
        payment_revenue = sum(order.get('price', 0) for order in payment_orders)

        # Top spending users
        user_spending = {}
        for order in completed_orders:
            user_id = str(order.get('user_id', ''))
            if user_id:
                user_spending[user_id] = user_spending.get(user_id, 0) + order.get('price', 0)

        top_spenders = []
        for user_id, spent_amount in sorted(user_spending.items(), key=lambda x: x[1], reverse=True)[:3]:
            user_data = users.get(user_id, {})
            username = user_data.get('username', f'User_{user_id}')
            top_spenders.append({
                'user_id': user_id,
                'username': username,
                'total_spent': spent_amount,
                'order_count': len([o for o in completed_orders if str(o.get('user_id', '')) == user_id])
            })

        # Agent statistics
        settings = self._load_json(self.settings_file)
        agents = settings.get('agents', {})
        total_agents = len(agents)
        total_agent_earnings = sum(agent.get('total_earnings', 0) for agent in agents.values())
        active_agents = len([agent for agent in agents.values() if agent.get('total_earnings', 0) > 0])

        return {
            'total_users': total_users,
            'total_balance': total_balance,
            'total_user_balance': total_balance,  # مجموع أرصدة المستخدمين
            'total_user_spending': total_revenue,  # مجموع إنفاق المستخدمين (الإيرادات المكتملة)
            'top_3_users': top_3_users,
            'banned_users': banned_users,
            'frozen_users': frozen_users,
            # Financial statistics
            'total_orders': total_orders,
            'completed_orders_count': len(completed_orders),
            'pending_orders_count': len(pending_orders),
            'rejected_orders_count': len(rejected_orders),
            'total_revenue': total_revenue,
            'pending_revenue': pending_revenue,
            'avg_order_value': avg_order_value,
            # Revenue by service type
            'app_orders_count': len(app_orders),
            'game_orders_count': len(game_orders),
            'payment_orders_count': len(payment_orders),
            'app_revenue': app_revenue,
            'game_revenue': game_revenue,
            'payment_revenue': payment_revenue,
            # Top spenders
            'top_spenders': top_spenders,
            # Agent statistics
            'total_agents': total_agents,
            'active_agents': active_agents,
            'total_agent_earnings': total_agent_earnings
        }

    def ban_user(self, user_id: int) -> bool:
        """Ban a user"""
        users = self._load_json(self.users_file)
        if str(user_id) in users:
            users[str(user_id)]['is_banned'] = True
            users[str(user_id)]['banned_at'] = datetime.now().isoformat()
            self._save_json(self.users_file, users)
            return True
        return False

    def unban_user(self, user_id: int) -> bool:
        """Unban a user"""
        users = self._load_json(self.users_file)
        if str(user_id) in users:
            users[str(user_id)]['is_banned'] = False
            users[str(user_id)].pop('banned_at', None)
            self._save_json(self.users_file, users)
            return True
        return False

    def is_user_banned(self, user_id: int) -> bool:
        """Check if user is banned"""
        users = self._load_json(self.users_file)
        user_data = users.get(str(user_id), {})
        return user_data.get('is_banned', False)

    def freeze_user(self, user_id: int, duration_minutes: int) -> bool:
        """Freeze a user for specific duration"""
        users = self._load_json(self.users_file)
        if str(user_id) in users:
            freeze_until = datetime.now() + timedelta(minutes=duration_minutes)
            users[str(user_id)]['frozen_until'] = freeze_until.isoformat()
            self._save_json(self.users_file, users)
            return True
        return False

    def unfreeze_user(self, user_id: int) -> bool:
        """Unfreeze a user"""
        users = self._load_json(self.users_file)
        if str(user_id) in users:
            users[str(user_id)].pop('frozen_until', None)
            self._save_json(self.users_file, users)
            return True
        return False

    def is_user_frozen(self, user_id: int) -> bool:
        """Check if user is currently frozen"""
        users = self._load_json(self.users_file)
        user_data = users.get(str(user_id), {})

        frozen_until_str = user_data.get('frozen_until')
        if not frozen_until_str:
            return False

        try:
            frozen_until = datetime.fromisoformat(frozen_until_str)
            return datetime.now() < frozen_until
        except:
            return False

    def delete_user(self, user_id: int) -> bool:
        """Delete a user completely"""
        users = self._load_json(self.users_file)
        if str(user_id) in users:
            del users[str(user_id)]
            self._save_json(self.users_file, users)
            return True
        return False

    def update_user_balance_silent(self, user_id: int, new_balance: int):
        """Update user balance without notification"""
        users = self._load_json(self.users_file)
        if str(user_id) not in users:
            self.get_user(user_id)  # Create user if doesn't exist
            users = self._load_json(self.users_file)

        users[str(user_id)]["balance"] = new_balance
        self._save_json(self.users_file, users)

    def get_user_details(self, user_id: int) -> Optional[Dict]:
        """Get detailed user information"""
        users = self._load_json(self.users_file)
        user_data = users.get(str(user_id))

        if user_data:
            user_data['user_id'] = user_id
            user_data['is_frozen'] = self.is_user_frozen(user_id)
            if user_data['is_frozen']:
                frozen_until = datetime.fromisoformat(user_data.get('frozen_until'))
                user_data['frozen_until_formatted'] = frozen_until.strftime('%Y-%m-%d %H:%M:%S')

        return user_data

    def search_user(self, query: str) -> List[Dict]:
        """Search users by ID or username"""
        users = self._load_json(self.users_file)
        results = []

        for user_id, user_data in users.items():
            # Search by user ID
            if query in user_id:
                user_info = user_data.copy()
                user_info['user_id'] = int(user_id)
                results.append(user_info)
            # Search by username if available
            elif 'username' in user_data and query.lower() in user_data['username'].lower():
                user_info = user_data.copy()
                user_info['user_id'] = int(user_id)
                results.append(user_info)

        return results[:10]  # Limit to 10 results

    def get_agents(self) -> Dict:
        """Get all agents"""
        settings = self._load_json(self.settings_file)
        return settings.get("agents", {})

    def add_agent(self, agent_id: str, name: str, user_id: int, commission_rate: float):
        """Add new agent"""
        settings = self._load_json(self.settings_file)
        if "agents" not in settings:
            settings["agents"] = {}

        settings["agents"][agent_id] = {
            "name": name,
            "user_id": user_id,
            "commission_rate": commission_rate,
            "total_earnings": 0,
            "total_orders": 0,
            "created_at": datetime.now().isoformat()
        }
        self._save_json(self.settings_file, settings)

    def update_agent(self, agent_id: str, data: Dict) -> bool:
        """Update agent data"""
        settings = self._load_json(self.settings_file)
        agents = settings.get("agents", {})

        if agent_id in agents:
            agents[agent_id].update(data)
            self._save_json(self.settings_file, settings)
            return True
        return False

    def delete_agent(self, agent_id: str) -> bool:
        """Delete agent"""
        settings = self._load_json(self.settings_file)
        agents = settings.get("agents", {})

        if agent_id in agents:
            del settings["agents"][agent_id]
            self._save_json(self.settings_file, settings)
            return True
        return False

    def get_agent_by_user_id(self, user_id: int) -> Optional[Dict]:
        """Get agent data by user ID"""
        settings = self._load_json(self.settings_file)
        agents = settings.get("agents", {})

        for agent_id, agent_data in agents.items():
            if agent_data.get("user_id") == user_id:
                agent_data["agent_id"] = agent_id
                return agent_data
        return None

    def add_agent_earnings(self, user_id: int, amount: float) -> bool:
        """Add earnings to agent account"""
        settings = self._load_json(self.settings_file)
        agents = settings.get("agents", {})

        for agent_id, agent_data in agents.items():
            if agent_data.get("user_id") == user_id:
                agents[agent_id]["total_earnings"] += amount
                agents[agent_id]["total_orders"] += 1
                self._save_json(self.settings_file, settings)
                return True
        return False

    def withdraw_agent_earnings(self, user_id: int) -> Optional[float]:
        """Withdraw agent earnings and return the amount"""
        settings = self._load_json(self.settings_file)
        agents = settings.get("agents", {})

        for agent_id, agent_data in agents.items():
            if agent_data.get("user_id") == user_id:
                earnings = agent_data.get("total_earnings", 0)
                if earnings > 0:
                    agents[agent_id]["total_earnings"] = 0
                    self._save_json(self.settings_file, settings)
                    return earnings
        return None

    def get_withdrawal_fees(self) -> float:
        """Get withdrawal fees percentage"""
        settings = self._load_json(self.settings_file)
        return settings.get("withdrawal_fees", 0)

    def set_withdrawal_fees(self, fees: float):
        """Set withdrawal fees percentage"""
        settings = self._load_json(self.settings_file)
        settings["withdrawal_fees"] = fees
        self._save_json(self.settings_file, settings)

    def get_bot_name(self, english: bool = False) -> str:
        """Get bot name (Arabic or English)"""
        settings = self._load_json(self.settings_file)
        if english:
            return settings.get("bot_name_english", "Lodoxa")
        return settings.get("bot_name", "لودوكسا")

    def set_bot_name(self, arabic_name: str, english_name: str):
        """Set bot name (both Arabic and English)"""
        settings = self._load_json(self.settings_file)
        settings["bot_name"] = arabic_name
        settings["bot_name_english"] = english_name
        self._save_json(self.settings_file, settings)

    def get_admins(self) -> Dict:
        """Get all admins"""
        settings = self._load_json(self.settings_file)
        return settings.get("admins", {})

    def add_admin(self, user_id: int, name: str):
        """Add new admin"""
        settings = self._load_json(self.settings_file)
        if "admins" not in settings:
            settings["admins"] = {}

        admin_id = f"admin_{user_id}"
        settings["admins"][admin_id] = {
            "user_id": user_id,
            "name": name,
            "created_at": datetime.now().isoformat()
        }
        self._save_json(self.settings_file, settings)

    def delete_admin(self, admin_id: str) -> bool:
        """Delete admin"""
        settings = self._load_json(self.settings_file)
        admins = settings.get("admins", {})

        if admin_id in admins:
            del settings["admins"][admin_id]
            self._save_json(self.settings_file, settings)
            return True
        return False

    def is_user_admin(self, user_id: int) -> bool:
        """Check if user is an admin"""
        if user_id == ADMIN_ID or user_id == ADMG01C:
            return True

        admins = self.get_admins()
        for admin_data in admins.values():
            if admin_data.get("user_id") == user_id:
                return True
        return False

    def get_user_by_referral_id(self, referral_id: int) -> Optional[Dict]:
        """Get user by referral ID"""
        users = self._load_json(self.users_file)
        for user_id, user_data in users.items():
            if user_data.get("referral_id") == referral_id:
                return {"user_id": int(user_id), "data": user_data}
        return None

    def set_referral_parent(self, user_id: int, parent_referral_id: int) -> bool:
        """Set who referred this user"""
        users = self._load_json(self.users_file)
        if str(user_id) not in users:
            return False

        parent = self.get_user_by_referral_id(parent_referral_id)
        if not parent:
            return False

        parent_user_id = parent["user_id"]
        if str(parent_user_id) not in users:
            return False

        users[str(user_id)]["referred_by"] = parent_user_id

        if user_id not in users[str(parent_user_id)]["referrals_level_1"]:
            users[str(parent_user_id)]["referrals_level_1"].append(user_id)

        grandparent_id = users[str(parent_user_id)].get("referred_by")
        if grandparent_id and str(grandparent_id) in users:
            if user_id not in users[str(grandparent_id)]["referrals_level_2"]:
                users[str(grandparent_id)]["referrals_level_2"].append(user_id)

        self._save_json(self.users_file, users)
        return True

    def add_referral_earnings(self, user_id: int, amount: float, from_user_id: int = None, level: int = 1) -> bool:
        """Add referral earnings to user"""
        users = self._load_json(self.users_file)
        if str(user_id) not in users:
            return False

        users[str(user_id)]["referral_earnings"] += amount
        users[str(user_id)]["total_referral_earnings"] += amount
        self._save_json(self.users_file, users)

        # Log the earning transaction
        from_ref_id = None
        if from_user_id:
            from_user = users.get(str(from_user_id))
            if from_user:
                from_ref_id = from_user.get('referral_id', from_user_id)

        description = f"أرباح من إحالة مستوى {level}"
        if from_ref_id:
            description += f" - المستخدم REF_{from_ref_id}"

        self.log_referral_transaction(
            user_id=user_id,
            transaction_type="earning",
            amount=amount,
            description=description,
            from_user_id=from_user_id,
            level=level
        )

        return True

    def withdraw_referral_earnings(self, user_id: int) -> Optional[float]:
        """Withdraw referral earnings to main balance"""
        users = self._load_json(self.users_file)
        if str(user_id) not in users:
            return None

        earnings = users[str(user_id)].get("referral_earnings", 0)
        if earnings <= 0:
            return None

        users[str(user_id)]["balance"] += earnings
        users[str(user_id)]["referral_earnings"] = 0
        self._save_json(self.users_file, users)

        # Log the withdrawal transaction
        self.log_referral_transaction(
            user_id=user_id,
            transaction_type="withdrawal",
            amount=earnings,
            description="سحب أرباح الإحالة إلى الرصيد الرئيسي"
        )

        return earnings

    def mark_user_purchased(self, user_id: int) -> bool:
        """Mark that user has made a purchase. Returns True if this is the first purchase."""
        users = self._load_json(self.users_file)
        if str(user_id) not in users:
            return False

        was_first_purchase = not users[str(user_id)].get("has_purchased", False)
        users[str(user_id)]["has_purchased"] = True
        self._save_json(self.users_file, users)
        return was_first_purchase

    def get_referral_badge(self, user_id: int) -> str:
        """Get user's referral badge based on referral count"""
        users = self._load_json(self.users_file)
        if str(user_id) not in users:
            return "لا توجد شارة 💤"

        referral_count = len(users[str(user_id)].get("referrals_level_1", []))

        if referral_count >= 50:
            return "شريك ذهبي 🟡"
        elif referral_count >= 20:
            return "خبير تسويق 🔵"
        elif referral_count >= 5:
            return "مسوّق مبتدئ 🟢"
        else:
            return "لا توجد شارة 💤"

    def get_referral_stats(self, user_id: int) -> Dict:
        """Get user's referral statistics"""
        users = self._load_json(self.users_file)
        if str(user_id) not in users:
            return {
                "referral_id": 0,
                "referrals_count": 0,
                "active_referrals_count": 0,
                "earnings": 0,
                "total_earnings": 0,
                "badge": "لا توجد شارة 💤",
                "has_purchased": False
            }

        user_data = users[str(user_id)]
        referrals_level_1 = user_data.get("referrals_level_1", [])

        # Count active referrals (those who have made at least one purchase)
        active_count = 0
        for ref_user_id in referrals_level_1:
            ref_user = users.get(str(ref_user_id))
            if ref_user and ref_user.get("has_purchased", False):
                active_count += 1

        return {
            "referral_id": user_data.get("referral_id", 0),
            "referrals_count": len(referrals_level_1),
            "active_referrals_count": active_count,
            "earnings": user_data.get("referral_earnings", 0),
            "total_earnings": user_data.get("total_referral_earnings", 0),
            "badge": self.get_referral_badge(user_id),
            "has_purchased": user_data.get("has_purchased", False)
        }

    def get_referral_settings(self) -> Dict:
        """Get referral system settings"""
        settings = self._load_json(self.settings_file)
        return {
            "enabled": settings.get("referral_enabled", True),
            "level_1_percentage": settings.get("referral_level_1_percentage", 1.0),
            "level_2_percentage": settings.get("referral_level_2_percentage", 0.5)
        }

    def set_referral_settings(self, enabled: bool = None, level_1: float = None, level_2: float = None):
        """Set referral system settings"""
        settings = self._load_json(self.settings_file)

        if enabled is not None:
            settings["referral_enabled"] = enabled
        if level_1 is not None:
            settings["referral_level_1_percentage"] = level_1
        if level_2 is not None:
            settings["referral_level_2_percentage"] = level_2

        self._save_json(self.settings_file, settings)

    def log_referral_transaction(self, user_id: int, transaction_type: str, amount: float,
                                 description: str, from_user_id: int = None, level: int = None):
        """Log a referral transaction (earning or withdrawal)"""
        from datetime import datetime
        import uuid

        logs = self._load_json(self.referral_logs_file)

        # Generate unique transaction ID
        transaction_id = str(uuid.uuid4())[:8]

        # Create transaction record
        transaction = {
            "transaction_id": transaction_id,
            "user_id": user_id,
            "type": transaction_type,  # "earning" or "withdrawal"
            "amount": amount,
            "description": description,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "from_user_id": from_user_id,
            "level": level
        }

        # Add to user's transaction log
        if str(user_id) not in logs:
            logs[str(user_id)] = []

        logs[str(user_id)].append(transaction)
        self._save_json(self.referral_logs_file, logs)

    def get_referral_transactions(self, user_id: int, limit: int = 50) -> list:
        """Get user's referral transaction history"""
        logs = self._load_json(self.referral_logs_file)

        if str(user_id) not in logs:
            return []

        # Return latest transactions first
        transactions = logs[str(user_id)]
        return list(reversed(transactions[-limit:]))

    def get_all_referral_transactions(self, limit: int = 100) -> list:
        """Get all referral transactions across all users"""
        logs = self._load_json(self.referral_logs_file)

        all_transactions = []
        for user_id, user_logs in logs.items():
            for transaction in user_logs:
                transaction['user_id'] = int(user_id)
                all_transactions.append(transaction)

        # Sort by timestamp (newest first)
        all_transactions.sort(key=lambda x: x['timestamp'], reverse=True)
        return all_transactions[:limit]

    def edit_user_referrals(self, user_id: int, new_referral_count: int = None, new_earnings: float = None):
        """Admin function to edit user's referral data"""
        users = self._load_json(self.users_file)
        if str(user_id) not in users:
            return False

        if new_earnings is not None:
            users[str(user_id)]["referral_earnings"] = new_earnings

        self._save_json(self.users_file, users)
        return True

# Initialize data manager
data_manager = DataManager()

class LodoxaBot:
    """Main bot class handling all interactions"""

    def __init__(self):
        self.current_service = {}
        self.current_selection = {}
        self.order_data = {}

    async def check_channel_subscription(self, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check if user is subscribed to the required channel"""
        try:
            member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
            return member.status in ['member', 'administrator', 'creator']
        except Exception as e:
            logger.error(f"Error checking channel subscription: {e}")
            return False

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start command handler"""
        user = update.effective_user

        # Check if bot is enabled (only for non-admin users)
        if user.id != ADMIN_ID and not data_manager.is_bot_enabled():
            await update.message.reply_text("البوت متوقف حالياً...حاول لاحقاً ⏳")
            return ConversationHandler.END

        # Check if user is banned (only for non-admin users)
        if user.id != ADMIN_ID and data_manager.is_user_banned(user.id):
            await update.message.reply_text("❌ تم حظر حسابك من استخدام البوت")
            return ConversationHandler.END

        # Check if user is frozen (only for non-admin users)
        if user.id != ADMIN_ID and data_manager.is_user_frozen(user.id):
            user_data = data_manager.get_user_details(user.id)
            frozen_until = user_data.get('frozen_until_formatted', 'غير محدد')
            await update.message.reply_text(f"🥶 تم تجميد حسابك حتى: {frozen_until}")
            return ConversationHandler.END

        # Check channel subscription first
        is_subscribed = await self.check_channel_subscription(user.id, context)

        if not is_subscribed:
            # Subscription required message
            subscription_text = f"""يجب الأشتراك في القناة: {CHANNEL_USERNAME}
لتتمكن من متابعة استخدام البوت 💜

أهلا وسهلا {user.first_name} 💜💜"""

            # Create subscription keyboard with dynamic channel URL from CHANNEL_USERNAME
            # Remove @ if exists and create proper Telegram link
            channel_username_clean = CHANNEL_USERNAME.lstrip('@')
            channel_url = f"https://t.me/{channel_username_clean}"

            keyboard = [[InlineKeyboardButton("الأشتراك في القناة 📢", url=channel_url)],
                       [InlineKeyboardButton("تحقق من الأشتراك ✅", callback_data="check_subscription")]]

            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                subscription_text,
                reply_markup=reply_markup
            )
            return MAIN_MENU

        # Check if this is a new user and send details to channel
        users = data_manager._load_json(data_manager.users_file)
        is_new_user = str(user.id) not in users

        # User is subscribed, show main menu
        user_data = data_manager.get_user(user.id)

        # Handle referral link if present
        referrer_user_id = None
        if context.args and len(context.args) > 0:
            ref_arg = context.args[0]
            if ref_arg.startswith("REF_"):
                try:
                    referral_id = int(ref_arg.replace("REF_", ""))
                    if is_new_user:
                        success = data_manager.set_referral_parent(user.id, referral_id)
                        if success:
                            logger.info(f"User {user.id} referred by ID {referral_id}")

                            # Get the referrer's user ID
                            referrer_info = data_manager.get_user_by_referral_id(referral_id)
                            if referrer_info:
                                referrer_user_id = referrer_info["user_id"]

                                # Send notification to the new user
                                try:
                                    await context.bot.send_message(
                                        chat_id=user.id,
                                        text=f"✨ لقد سجلت بإستخدام رابط إحالة صديقك **#{referral_id}**",
                                        parse_mode='Markdown'
                                    )
                                except Exception as e:
                                    logger.error(f"Failed to send referral welcome to new user {user.id}: {e}")

                                # Send notification to the referrer
                                # Get the new user's referral ID
                                new_user_data = data_manager.get_user(user.id)
                                new_user_ref_id = new_user_data.get('referral_id', user.id)

                                try:
                                    await context.bot.send_message(
                                        chat_id=referrer_user_id,
                                        text=f"🎉 مستخدم جديد قام بالتسجيل من خلال رابط إحالتك ⚡\n\n👤 المستخدم: REF_{new_user_ref_id}",
                                        parse_mode='Markdown'
                                    )
                                except Exception as e:
                                    logger.error(f"Failed to send referral notification to referrer {referrer_user_id}: {e}")
                except ValueError:
                    logger.warning(f"Invalid referral ID format: {ref_arg}")

        # Send new user details to channel if this is a new user
        if is_new_user:
            await self.send_new_user_to_channel(context, user)

        bot_name = data_manager.get_bot_name(english=False)
        welcome_text = f"""🎮 أهلاً بك في متجر {bot_name} 💰
أسرع منصة للشحن الإلكتروني في سوريا 🇸🇾
──────────────────────────
💳 معرفك: `{user.id}`
💵 رصيدك: **{user_data['balance']:,.2f} SYP**"""

        # Create keyboard
        keyboard = [
            [KeyboardButton("شحن تطبيق 📱"), KeyboardButton("شحن لعبة 🎮")],
            [KeyboardButton("شحن رصيد حسابك ➕"), KeyboardButton("تواصل مع الدعم 💬")]
        ]

        # Add referral button if system is enabled
        referral_settings = data_manager.get_referral_settings()
        if referral_settings["enabled"]:
            keyboard.append([KeyboardButton("نظام الإحالة 🎁")])

        # Add admin panel for all admins (including those added via ADMG01C)
        if data_manager.is_user_admin(user.id):
            keyboard.append([KeyboardButton("لوحة التحكم 🛠")])

        # Add ADMG01C panel for special admin
        if ADMG01C > 0 and user.id == ADMG01C:
            keyboard.append([KeyboardButton("ADMG01C ⚙️")])

        # Add agent panel for agents
        agent_data = data_manager.get_agent_by_user_id(user.id)
        if agent_data:
            keyboard.append([KeyboardButton("لوحة الوكيل 🤝")])

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        # Create inline keyboard for statistics button integrated with welcome message
        inline_keyboard = [[InlineKeyboardButton("📊 بياناتي", callback_data="show_my_statistics")]]
        inline_markup = InlineKeyboardMarkup(inline_keyboard)

        await update.message.reply_text(
            welcome_text,
            reply_markup=inline_markup,
            parse_mode='Markdown'
        )

        # Send keyboard-only message
        await update.message.reply_text(
            "اختر خدمة:",
            reply_markup=reply_markup
        )

        return MAIN_MENU

    async def handle_subscription_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle subscription check callback"""
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        is_subscribed = await self.check_channel_subscription(user_id, context)

        if is_subscribed:
            # User is now subscribed, show main menu
            user = update.effective_user
            user_data = data_manager.get_user(user.id)

            bot_name = data_manager.get_bot_name(english=False)
            welcome_text = f"""🎮 أهلاً بك في متجر {bot_name} 💰
أسرع منصة للشحن الإلكتروني في سوريا 🇸🇾
──────────────────────────
💳 معرفك: `{user.id}`
💵 رصيدك: **{user_data['balance']:,.2f} SYP**"""

            # Create keyboard
            keyboard = [
                [KeyboardButton("شحن تطبيق 📱"), KeyboardButton("شحن لعبة 🎮")],
                [KeyboardButton("شحن رصيد حسابك ➕"), KeyboardButton("تواصل مع الدعم 💬")]
            ]

            # Add referral button if system is enabled
            referral_settings = data_manager.get_referral_settings()
            if referral_settings["enabled"]:
                keyboard.append([KeyboardButton("نظام الإحالة 🎁")])

            # Add admin panel for all admins (including those added via ADMG01C)
            if data_manager.is_user_admin(user.id):
                keyboard.append([KeyboardButton("لوحة التحكم 🛠")])

            # Add ADMG01C panel for special admin
            if ADMG01C > 0 and user.id == ADMG01C:
                keyboard.append([KeyboardButton("ADMG01C ⚙️")])

            # Add agent panel for agents
            agent_data = data_manager.get_agent_by_user_id(user.id)
            if agent_data:
                keyboard.append([KeyboardButton("لوحة الوكيل 🤝")])

            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

            # Create inline keyboard for statistics button
            inline_keyboard = [[InlineKeyboardButton("📊 بياناتي", callback_data="show_my_statistics")]]
            inline_markup = InlineKeyboardMarkup(inline_keyboard)

            await query.edit_message_text(
                welcome_text,
                reply_markup=inline_markup,
                parse_mode='Markdown'
            )

            # Send a new message with the keyboard since we can't edit keyboard through callback
            await context.bot.send_message(
                chat_id=user.id,
                text="اختر خدمة:",
                reply_markup=reply_markup
            )

            return MAIN_MENU
        else:
            # Still not subscribed
            await query.answer("يرجى الأشتراك في القناة أولاً 💜", show_alert=True)
            return MAIN_MENU

    async def handle_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle main menu selection"""
        text = update.message.text
        user_id = update.effective_user.id

        # Check if bot is enabled (only for non-admin users)
        if not data_manager.is_user_admin(user_id) and not data_manager.is_bot_enabled():
            await update.message.reply_text("البوت متوقف حالياً...حاول لاحقاً ⏳")
            return ConversationHandler.END

        # Check subscription before processing any request
        is_subscribed = await self.check_channel_subscription(user_id, context)
        if not is_subscribed:
            return await self.start(update, context)

        if text == "شحن تطبيق 📱":
            # Clear any previous data before starting new operation
            context.user_data.clear()
            context.user_data['service_type'] = 'app'
            return await self.show_apps_games(update, context, 'app')

        elif text == "شحن لعبة 🎮":
            # Clear any previous data before starting new operation
            context.user_data.clear()
            context.user_data['service_type'] = 'game'
            return await self.show_apps_games(update, context, 'game')

        elif text == "شحن رصيد حسابك ➕":
            user_data = data_manager.get_user(user_id)
            bot_name = data_manager.get_bot_name(english=False)

            message = f"💰 **شحن الرصيد - {bot_name}**\n\n"
            message += f"💵 رصيدك الحالي: **{user_data['balance']:,.2f} SYP**\n\n"
            message += "اختر طريقة الدفع المناسبة لك:"

            keyboard = [
                [KeyboardButton("سيريتل كاش 📱")],
                [KeyboardButton("شام كاش | Sham Cash")],
                [KeyboardButton("Payeer 💳"), KeyboardButton("USDT BEP-20 🪙")],
                [KeyboardButton("كود شحن 🏷️")],
                [KeyboardButton("⬅️ العودة للقائمة الرئيسية")]
            ]

            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            return SELECTING_PAYMENT_METHOD

        elif text == "تواصل مع الدعم 💬":
            support_username = data_manager.get_support_username()
            if support_username:
                await update.message.reply_text(
                    f"يمكنك التواصل مع الدعم من هنا: @{support_username}"
                )
            else:
                await update.message.reply_text(
                    "لم يتم تعيين حساب دعم بعد. يرجى المحاولة لاحقاً."
                )
            return MAIN_MENU

        elif text == "لوحة التحكم 🛠" and data_manager.is_user_admin(user_id):
            return await self.show_admin_panel(update, context)

        elif text == "ADMG01C ⚙️" and ADMG01C > 0 and user_id == ADMG01C:
            return await self.show_admg01c_panel(update, context)

        elif text == "لوحة الوكيل 🤝":
            agent_data = data_manager.get_agent_by_user_id(user_id)
            if agent_data:
                return await self.show_agent_panel(update, context, agent_data)
            else:
                await update.message.reply_text("غير مصرح لك بالوصول لهذه الخدمة.")
                return MAIN_MENU

        elif text == "نظام الإحالة 🎁":
            return await self.show_referral_page(update, context)

        else:
            await update.message.reply_text("يرجى اختيار خدمة من القائمة:")
            return MAIN_MENU

    async def show_referral_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show referral system page"""
        user_id = update.effective_user.id

        referral_stats = data_manager.get_referral_stats(user_id)
        referral_settings = data_manager.get_referral_settings()

        if not referral_settings["enabled"]:
            await update.message.reply_text("نظام الإحالة غير مفعل حالياً.")
            return MAIN_MENU

        bot_info = await context.bot.get_me()
        bot_username = bot_info.username

        referral_link = f"https://t.me/{bot_username}?start=REF_{referral_stats['referral_id']}"

        message = f"""🎁 نظام الإحالة

شارة الحساب: {referral_stats['badge']}

💰 ستحصل على {referral_settings['level_1_percentage']}% من كل عملية شحن ناجحة من خلال إحالتك
و {referral_settings['level_2_percentage']}% من خلال إحالة المستوى الثاني.

🔗 رابط إحالتك:
{referral_link}

📊 إحصائيات الإحالات:
👥 عدد الإحالات الكلي: {referral_stats['referrals_count']}
⚡ عدد الإحالات الفعالة: {referral_stats['active_referrals_count']}

💵 مجموع أرباحك: {referral_stats['earnings']:,.2f} SYP"""

        keyboard = []

        if referral_stats['earnings'] > 0:
            keyboard.append([InlineKeyboardButton("💸 سحب أرباح الإحالة إلى الرصيد الرئيسي", callback_data="withdraw_referral_earnings")])

        keyboard.append([InlineKeyboardButton("⬅️ العودة للقائمة الرئيسية", callback_data="back_to_main_menu")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup)

        return MAIN_MENU

    async def handle_withdraw_referral_earnings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle withdrawal of referral earnings"""
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id

        earnings = data_manager.withdraw_referral_earnings(user_id)

        if earnings is None:
            await query.edit_message_text("❌ لا توجد أرباح متاحة للسحب.")
            return MAIN_MENU

        message = f"""✅ تم سحب أرباح الإحالة بنجاح!

💵 المبلغ المحول: **{earnings:,.2f} SYP**
💰 تم إضافته إلى رصيدك الرئيسي

رصيدك الجديد: **{data_manager.get_user(user_id)['balance']:,.2f} SYP**"""

        await query.edit_message_text(message, parse_mode='Markdown')

        return MAIN_MENU

    async def handle_back_to_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle back to main menu from inline buttons"""
        query = update.callback_query
        await query.answer()

        # Clear user data
        context.user_data.clear()

        # Delete the current message
        try:
            await query.delete_message()
        except Exception:
            pass

        # Get user info and show main menu
        user_id = update.effective_user.id
        user = data_manager.get_user(user_id)
        bot_name = data_manager.get_bot_name(english=False)

        welcome_text = f"""🎮 أهلاً بك في متجر {bot_name} 💰
أسرع منصة للشحن الإلكتروني في سوريا 🇸🇾
──────────────────────────
💳 معرفك: `{user_id}`
💵 رصيدك: **{user['balance']:,.2f} SYP**"""

        # Create keyboard
        keyboard = [
            [KeyboardButton("شحن تطبيق 📱"), KeyboardButton("شحن لعبة 🎮")],
            [KeyboardButton("شحن رصيد حسابك ➕"), KeyboardButton("تواصل مع الدعم 💬")]
        ]

        # Add referral button if system is enabled
        referral_settings = data_manager.get_referral_settings()
        if referral_settings["enabled"]:
            keyboard.append([KeyboardButton("نظام الإحالة 🎁")])

        # Add admin panel for all admins
        if data_manager.is_user_admin(user_id):
            keyboard.append([KeyboardButton("لوحة التحكم 🛠")])

        # Add ADMG01C panel for special admin
        if ADMG01C > 0 and user_id == ADMG01C:
            keyboard.append([KeyboardButton("ADMG01C ⚙️")])

        # Add agent panel for agents
        agent_data = data_manager.get_agent_by_user_id(user_id)
        if agent_data:
            keyboard.append([KeyboardButton("لوحة الوكيل 🤝")])

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        inline_keyboard = [[InlineKeyboardButton("📊 بياناتي", callback_data="show_my_statistics")]]
        inline_markup = InlineKeyboardMarkup(inline_keyboard)

        await query.message.reply_text(
            welcome_text,
            reply_markup=inline_markup,
            parse_mode='Markdown'
        )

        await query.message.reply_text(
            "اختر خدمة:",
            reply_markup=reply_markup
        )

        return MAIN_MENU

    async def show_apps_games(self, update: Update, context: ContextTypes.DEFAULT_TYPE, service_type: str) -> int:
        """Show available apps or games"""
        if service_type == 'app':
            items = data_manager.get_apps()
            message = "أختر التطبيق المراد شحنه:"
        else:
            items = data_manager.get_games()
            message = "أختر اللعبة المراد شحنها:"

        if not items:
            await update.message.reply_text("لا توجد خدمات متاحة حالياً.")
            return MAIN_MENU

        # Create inline keyboard with 2 buttons per row
        keyboard = []
        buttons_row = []
        for item_id, item_data in items.items():
            # Make sure the callback data is properly formatted
            callback_data = f"select_{service_type}_{item_id}"
            logger.info(f"Creating button for {item_data['name']} with callback: {callback_data}")
            buttons_row.append(InlineKeyboardButton(item_data['name'], callback_data=callback_data))

            # Add row when we have 2 buttons or when it's the last item
            if len(buttons_row) == 2:
                keyboard.append(buttons_row)
                buttons_row = []

        # Add remaining button if any
        if buttons_row:
            keyboard.append(buttons_row)

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup)

        return SELECTING_APP_GAME

    async def show_apps_games_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, service_type: str) -> int:
        """Show available apps or games for callback queries"""
        if service_type == 'app':
            items = data_manager.get_apps()
            message = "أختر التطبيق المراد شحنه:"
        else:
            items = data_manager.get_games()
            message = "أختر اللعبة المراد شحنها:"

        if not items:
            await update.callback_query.edit_message_text("لا توجد خدمات متاحة حالياً.")
            return MAIN_MENU

        # Create inline keyboard with 2 buttons per row
        keyboard = []
        buttons_row = []
        for item_id, item_data in items.items():
            # Make sure the callback data is properly formatted
            callback_data = f"select_{service_type}_{item_id}"
            logger.info(f"Creating callback button for {item_data['name']} with callback: {callback_data}")
            buttons_row.append(InlineKeyboardButton(item_data['name'], callback_data=callback_data))

            # Add row when we have 2 buttons or when it's the last item
            if len(buttons_row) == 2:
                keyboard.append(buttons_row)
                buttons_row = []

        # Add remaining button if any
        if buttons_row:
            keyboard.append(buttons_row)

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup)

        return SELECTING_APP_GAME

    async def handle_app_game_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle app/game selection"""
        query = update.callback_query
        await query.answer()

        # Parse callback data
        parts = query.data.split('_')
        service_type = parts[1]  # 'app' or 'game'
        item_id = '_'.join(parts[2:])  # Join all remaining parts in case the ID contains underscores

        context.user_data['selected_item_id'] = item_id
        context.user_data['service_type'] = service_type

        # Get item data
        if service_type == 'app':
            items = data_manager.get_apps()
        else:
            items = data_manager.get_games()

        # Debug: print available items
        logger.info(f"Available {service_type}s: {list(items.keys())}")
        logger.info(f"Looking for item_id: {item_id}")

        item_data = items.get(item_id)
        if not item_data:
            # Try to find by exact match or partial match
            found_id = None
            for existing_id in items.keys():
                if existing_id == item_id or item_id in existing_id or existing_id in item_id:
                    found_id = existing_id
                    break

            if found_id:
                item_data = items[found_id]
                context.user_data['selected_item_id'] = found_id
            else:
                await query.edit_message_text(f"❌ التطبيق/اللعبة غير متاح حالياً.\n\nالمتاح: {', '.join(items.keys())}")
                return MAIN_MENU

        # Check if categories exist
        categories = item_data.get('categories', {})
        if not categories:
            service_name = "التطبيق" if service_type == 'app' else "اللعبة"
            await query.edit_message_text(f"❌ لا توجد فئات شحن متاحة لهذا {service_name} حالياً.")
            return MAIN_MENU

        # Show categories
        message = f"🎮 **{item_data['name']}**\n\nاختر فئة الشحن:"
        keyboard = []

        for cat_id, cat_data in categories.items():
            if cat_data.get('type') == 'fixed':
                button_text = f"{cat_data['name']} - {cat_data['price']:,} SYP"
            else:
                button_text = f"{cat_data['name']} - {cat_data['price_per_unit']:,} SYP/وحدة"

            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"category_{cat_id}")])

        keyboard.append([InlineKeyboardButton("⬅️ العودة", callback_data=f"back_to_{service_type}s")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return SELECTING_CATEGORY

    async def handle_category_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle category selection"""
        query = update.callback_query
        await query.answer()

        if query.data.startswith("back_to_"):
            service_type = query.data.split('_')[2].rstrip('s')
            return await self.show_apps_games_callback(update, context, service_type)

        category_id = query.data.replace("category_", "")
        context.user_data['selected_category_id'] = category_id

        # Get category data
        service_type = context.user_data['service_type']
        item_id = context.user_data['selected_item_id']

        if service_type == 'app':
            items = data_manager.get_apps()
        else:
            items = data_manager.get_games()

        item_data = items[item_id]
        category_data = item_data['categories'][category_id]

        if category_data['type'] == 'fixed':
            # Fixed price - go directly to account ID input
            context.user_data['final_price'] = category_data['price']
            context.user_data['quantity'] = 1

            message = f"🎮 الخدمة: {item_data['name']}\n\n"
            message += f"🏷️ الفئة: {category_data['name']}\n\n"
            message += f"💰 السعر: {category_data['price']:,} SYP\n\n"
            message += "يرجى إدخال معرف الحساب المراد شحنه:"

            await query.edit_message_text(message)
            return ENTERING_ACCOUNT_ID

        else:
            # Quantity-based pricing
            price_per_unit = category_data['price_per_unit']
            min_order = category_data.get('min_order', 1)
            max_order = category_data.get('max_order')

            context.user_data['price_per_unit'] = price_per_unit

            service_type_name = "شحن تطبيق" if service_type == 'app' else "شحن لعبة"
            message = f"📱 **القسم:** {service_type_name}\n\n"
            message += f"🎮 **الخدمة:** {item_data['name']}\n\n"
            message += f"🏷️ **الفئة:** {category_data['name']}\n\n"
            message += f"💰 **السعر لكل وحدة:** {price_per_unit:,} SYP\n\n"

            # Add min/max order limits if they exist
            if min_order:
                message += f"📊 **أقل طلب:** {min_order}\n\n"
            if max_order:
                message += f"📊 **أقصى طلب:** {max_order}\n\n"

            message += "📊 **أدخل الكمية المطلوبة:**"

            await query.edit_message_text(message, parse_mode='Markdown')
            # Store the message ID for later editing
            context.user_data['last_bot_message_id'] = query.message.message_id
            return ENTERING_QUANTITY

    async def handle_quantity_input_universal(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle quantity input for both apps/games and payment services"""
        # Check if this is for payment service or app/game
        if context.user_data.get('selected_payment_service'):
            return await self.handle_payment_quantity_input(update, context)
        else:
            return await self.handle_quantity_input(update, context)

    async def handle_quantity_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle quantity input for quantity-based pricing"""
        try:
            quantity = float(update.message.text)
            if quantity <= 0:
                raise ValueError

            # Get category data to check min/max limits
            service_type = context.user_data['service_type']
            item_id = context.user_data['selected_item_id']
            category_id = context.user_data['selected_category_id']

            if service_type == 'app':
                items = data_manager.get_apps()
            else:
                items = data_manager.get_games()

            item_data = items[item_id]
            category_data = item_data['categories'][category_id]

            # Check min/max order limits if they exist
            min_order = category_data.get('min_order')
            max_order = category_data.get('max_order')

            if min_order and quantity < min_order:
                await update.message.reply_text(f"أقل طلب مسموح: {min_order}. يرجى إدخال كمية أكبر:")
                return ENTERING_QUANTITY

            if max_order and quantity > max_order:
                await update.message.reply_text(f"أقصى طلب مسموح: {max_order}. يرجى إدخال كمية أقل:")
                return ENTERING_QUANTITY

            price_per_unit = context.user_data['price_per_unit']
            total_price = quantity * price_per_unit

            context.user_data['quantity'] = quantity
            context.user_data['final_price'] = total_price

            service_type_name = "شحن تطبيق" if service_type == 'app' else "شحن لعبة"
            message = f"📱 **القسم:** {service_type_name}\n\n"
            message += f"🎮 **الخدمة:** {item_data['name']}\n\n"
            message += f"🏷️ **الفئة:** {category_data['name']}\n\n"
            message += f"💰 **السعر لكل وحدة:** {price_per_unit:,} SYP\n\n"
            message += f"📊 **الكمية:** {quantity}\n\n"
            message += f"💰 **السعر الإجمالي:** {total_price:,.2f} SYP\n\n"
            message += "👤 **يرجى إدخال معرف الحساب المراد شحنه:**"

            # Check if there's a previous message to edit (from callback query)
            if hasattr(context.user_data, 'last_bot_message_id') and context.user_data.get('last_bot_message_id'):
                try:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=context.user_data['last_bot_message_id'],
                        text=message,
                        parse_mode='Markdown'
                    )
                except Exception:
                    # If editing fails, send a new message
                    sent_message = await update.message.reply_text(message, parse_mode='Markdown')
                    context.user_data['last_bot_message_id'] = sent_message.message_id
            else:
                sent_message = await update.message.reply_text(message, parse_mode='Markdown')
                context.user_data['last_bot_message_id'] = sent_message.message_id
            return ENTERING_ACCOUNT_ID

        except ValueError:
            await update.message.reply_text("يرجى إدخال كمية صحيحة (رقم موجب):")
            return ENTERING_QUANTITY

    async def handle_account_id_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle account ID input"""
        account_id = update.message.text.strip()
        context.user_data['account_id'] = account_id

        # Check if this is a payment service or regular app/game
        if context.user_data.get('selected_payment_service'):
            # This is a payment service
            return await self.show_payment_confirmation(update, context)
        else:
            # This is a regular app/game order
            service_type = context.user_data['service_type']
            item_id = context.user_data['selected_item_id']
            category_id = context.user_data['selected_category_id']

            if service_type == 'app':
                items = data_manager.get_apps()
            else:
                items = data_manager.get_games()

            item_data = items[item_id]
            category_data = item_data['categories'][category_id]

            # Create order summary without balance check
            service_type_name = "شحن تطبيق" if service_type == 'app' else "شحن لعبة"
            message = "📋 ملخص الطلب:\n\n"
            message += f"📱 القسم: {service_type_name}\n\n"
            message += f"🎮 الخدمة: {item_data['name']}\n\n"
            message += f"🏷️ الفئة: {category_data['name']}\n\n"

            if category_data['type'] == 'quantity':
                message += f"📊 الكمية: {context.user_data['quantity']}\n\n"

            message += f"🔑 معرف الحساب: {account_id}\n\n"
            message += f"💰 السعر الإجمالي: {context.user_data['final_price']:,} SYP\n\n"
            message += "هل تريد تأكيد الطلب؟"

            keyboard = [
                [InlineKeyboardButton("✅ تأكيد الطلب", callback_data="confirm_order")],
                [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_order")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup)

            return CONFIRMING_ORDER

    async def handle_order_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle order confirmation"""
        query = update.callback_query
        await query.answer()

        if query.data == "cancel_order":
            await query.edit_message_text("تم إلغاء الطلب.")
            return MAIN_MENU

        elif query.data == "confirm_order":
            user_id = update.effective_user.id
            user_data = data_manager.get_user(user_id)
            final_price = context.user_data['final_price']

            # Check balance only when user confirms the order
            if user_data['balance'] < final_price:
                await query.edit_message_text(
                    f"❌ رصيد حسابك غير كافي لإكمال العملية\n\n"
                    f"💰 رصيدك الحالي: {user_data['balance']:,.2f} SYP\n"
                    f"💸 سعر الطلب: {final_price:,.2f} SYP\n"
                    f"📊 تحتاج إلى: {final_price - user_data['balance']:,.2f} SYP إضافية"
                )
                return MAIN_MENU

            # Show processing message immediately
            await query.edit_message_text("⏳ جاري معالجة طلبك...")

            try:
                # Deduct balance
                data_manager.update_user_balance(user_id, -final_price)

                # Check if user is an agent and add commission
                agent_data = data_manager.get_agent_by_user_id(user_id)
                if agent_data:
                    commission_amount = final_price * (agent_data['commission_rate'] / 100)
                    data_manager.add_agent_earnings(user_id, commission_amount)

                # Generate unique order ID
                order_id = generate_order_id()

                # Create order with timestamp
                order_data = {
                    "order_id": order_id,
                    "user_id": user_id,
                    "username": update.effective_user.username or update.effective_user.first_name,
                    "service_type": context.user_data['service_type'],
                    "item_id": context.user_data['selected_item_id'],
                    "category_id": context.user_data['selected_category_id'],
                    "quantity": context.user_data.get('quantity', 1),
                    "account_id": context.user_data['account_id'],
                    "price": final_price,
                    "status": "قيد المعالجة",
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

                data_manager.save_order(order_data)

                # Send order to channel in background
                asyncio.create_task(self.send_order_to_channel(context, order_id, order_data))

                # Get order details for confirmation message
                service_type = context.user_data['service_type']
                item_id = context.user_data['selected_item_id']
                category_id = context.user_data['selected_category_id']

                if service_type == 'app':
                    items = data_manager.get_apps()
                else:
                    items = data_manager.get_games()

                item_data = items[item_id]
                category_data = item_data['categories'][category_id]

                # Create detailed confirmation message
                service_type_name = "شحن تطبيق" if service_type == 'app' else "شحن لعبة"
                confirmation_message = "📊 حالة الطلب: قيد المعالجة\n\n"
                confirmation_message += "📋 تفاصيل الطلب:\n\n"
                confirmation_message += f"📱 القسم: {service_type_name}\n\n"
                confirmation_message += f"🎮 الخدمة: {item_data['name']}\n\n"
                confirmation_message += f"🏷️ الفئة: {category_data['name']}\n\n"

                if category_data['type'] == 'quantity':
                    confirmation_message += f"📊 الكمية: {context.user_data['quantity']}\n\n"

                confirmation_message += f"🔑 معرف الحساب: {context.user_data['account_id']}\n\n"
                confirmation_message += f"💰 السعر الإجمالي: {final_price:,.2f} SYP\n\n"
                confirmation_message += f"🆔 رقم الطلب: {order_id}\n\n"
                confirmation_message += f"🕐 التاريخ والوقت: {order_data['timestamp']}\n\n"
                confirmation_message += "🔔 سيتم إشعارك عند تحديث حالة الطلب"

                # Send final confirmation
                await context.bot.edit_message_text(
                    chat_id=query.message.chat_id,
                    message_id=query.message.message_id,
                    text=confirmation_message
                )

            except Exception as e:
                logger.error(f"Error processing order: {e}")
                # Refund balance if there was an error
                data_manager.update_user_balance(user_id, final_price)
                await context.bot.edit_message_text(
                    chat_id=query.message.chat_id,
                    message_id=query.message.message_id,
                    text="❌ حدث خطأ في معالجة الطلب. تم إرجاع المبلغ لرصيدك."
                )
            finally:
                # Clear user data
                context.user_data.clear()

            return MAIN_MENU

    async def send_new_user_to_channel(self, context: ContextTypes.DEFAULT_TYPE, user):
        """Send new user details to notification channel"""
        # Create message with user details
        message = f"👤 مستخدم جديد انضم للبوت\n\n"
        message += f"🆔 معرف المستخدم: {user.id}\n"
        message += f"👤 الاسم الأول: {user.first_name or 'غير محدد'}\n"

        if user.last_name:
            message += f"👤 الاسم الأخير: {user.last_name}\n"

        if user.username:
            message += f"👨‍💻 اسم المستخدم: @{user.username}\n"
        else:
            message += f"👨‍💻 اسم المستخدم: غير محدد\n"

        message += f"🌐 اللغة: {user.language_code or 'غير محدد'}\n"
        message += f"📅 تاريخ الانضمام: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += f"🤖 نوع المستخدم: {'بوت' if user.is_bot else 'مستخدم عادي'}"

        # Try to send to notification channel
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                await context.bot.send_message(
                    chat_id=NEW_USER_CHANNEL,
                    text=message
                )
                logger.info(f"New user {user.id} details sent to notification channel successfully")
                return
            except Exception as e:
                logger.error(f"Failed to send new user {user.id} to notification channel (attempt {attempt + 1}): {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2)

        # If all attempts failed, log error
        logger.error(f"CRITICAL: Failed to notify about new user {user.id} after {max_attempts} attempts")

    async def send_order_to_channel(self, context: ContextTypes.DEFAULT_TYPE, order_id: str, order_data: Dict):
        """Send new order to orders channel"""
        # Get item details
        if order_data['service_type'] == 'app':
            items = data_manager.get_apps()
        else:
            items = data_manager.get_games()

        item_data = items[order_data['item_id']]
        category_data = item_data['categories'][order_data['category_id']]

        # Create message
        message = f"🔔 طلب جديد\n\n"
        message += f"🆔 رقم الطلب: {order_id}\n"
        message += f"👤 المستخدم: @{order_data['username'] or 'Unknown'} ({order_data['user_id']})\n"
        message += f"🎮 الخدمة: {item_data['name']}\n"
        message += f"📦 الفئة: {category_data['name']}\n"

        if order_data['quantity'] != 1:
            message += f"📊 الكمية: {order_data['quantity']}\n"

        message += f"🔑 معرف الحساب: {order_data['account_id']}\n"
        message += f"💰 السعر: {order_data['price']:,} SYP\n"
        message += f"📅 التاريخ والوقت: {order_data['timestamp']}\n"
        message += f"📊 الحالة: {order_data['status']}"

        keyboard = [
            [InlineKeyboardButton("✅ قبول", callback_data=f"approve_order_{order_id}")],
            [InlineKeyboardButton("❌ رفض", callback_data=f"reject_order_{order_id}")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Try to send to orders channel first
        max_attempts = 3
        channel_sent = False

        for attempt in range(max_attempts):
            try:
                await context.bot.send_message(
                    chat_id=ORDERS_CHANNEL,
                    text=message,
                    reply_markup=reply_markup
                )
                logger.info(f"Order {order_id} sent to orders channel successfully")
                channel_sent = True
                return
            except Exception as e:
                logger.error(f"Failed to send order {order_id} to channel (attempt {attempt + 1}): {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2)

        # If channel sending failed, fall back to admin
        if not channel_sent:
            logger.warning(f"Failed to send to orders channel, falling back to admin for order {order_id}")
            await self.notify_admin_new_order(context, order_id, order_data)

    async def notify_admin_new_order(self, context: ContextTypes.DEFAULT_TYPE, order_id: str, order_data: Dict):
        """Notify admin about new order (fallback method)"""
        # Get item details
        if order_data['service_type'] == 'app':
            items = data_manager.get_apps()
        else:
            items = data_manager.get_games()

        item_data = items[order_data['item_id']]
        category_data = item_data['categories'][order_data['category_id']]

        # Escape special characters for markdown
        def escape_markdown(text):
            special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in special_chars:
                text = str(text).replace(char, f'\\{char}')
            return text

        # Create message with escaped content
        message = f"🔔 طلب جديد\n\n"
        message += f"🆔 رقم الطلب: `{order_id}`\n"
        message += f"👤 المستخدم: @{escape_markdown(order_data['username'] or 'Unknown')} (`{order_data['user_id']}`)\n"
        message += f"🎮 الخدمة: {escape_markdown(item_data['name'])}\n"
        message += f"📦 الفئة: {escape_markdown(category_data['name'])}\n"

        if order_data['quantity'] != 1:
            message += f"📊 الكمية: `{order_data['quantity']}`\n"

        message += f"🔑 معرف الحساب: `{escape_markdown(order_data['account_id'])}`\n"
        message += f"💰 السعر: {order_data['price']:,} SYP\n"
        message += f"📅 التاريخ والوقت: {escape_markdown(order_data['timestamp'])}\n"
        message += f"📊 الحالة: {escape_markdown(order_data['status'])}"

        keyboard = [
            [InlineKeyboardButton("✅ قبول", callback_data=f"approve_order_{order_id}")],
            [InlineKeyboardButton("❌ رفض", callback_data=f"reject_order_{order_id}")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Try to send notification with multiple attempts and different formats
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                if attempt == 0:
                    # First attempt with MarkdownV2
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=message,
                        reply_markup=reply_markup,
                        parse_mode='MarkdownV2'
                    )
                elif attempt == 1:
                    # Second attempt with HTML
                    html_message = f"🔔 طلب جديد\n\n"
                    html_message += f"🆔 رقم الطلب: <code>{order_id}</code>\n"
                    html_message += f"👤 المستخدم: @{order_data['username'] or 'Unknown'} (<code>{order_data['user_id']}</code>)\n"
                    html_message += f"🎮 الخدمة: {item_data['name']}\n"
                    html_message += f"📦 الفئة: {category_data['name']}\n"

                    if order_data['quantity'] != 1:
                        html_message += f"📊 الكمية: <code>{order_data['quantity']}</code>\n"

                    html_message += f"🔑 معرف الحساب: <code>{order_data['account_id']}</code>\n"
                    html_message += f"💰 السعر: {order_data['price']:,} SYP\n"
                    html_message += f"📅 التاريخ والوقت: {order_data['timestamp']}\n"
                    html_message += f"📊 الحالة: {order_data['status']}"

                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=html_message,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                else:
                    # Third attempt without formatting
                    plain_message = f"🔔 طلب جديد\n\n"
                    plain_message += f"🆔 رقم الطلب: {order_id}\n"
                    plain_message += f"👤 المستخدم: @{order_data['username'] or 'Unknown'} ({order_data['user_id']})\n"
                    plain_message += f"🎮 الخدمة: {item_data['name']}\n"
                    plain_message += f"📦 الفئة: {category_data['name']}\n"

                    if order_data['quantity'] != 1:
                        plain_message += f"📊 الكمية: {order_data['quantity']}\n"

                    plain_message += f"🔑 معرف الحساب: {order_data['account_id']}\n"
                    plain_message += f"💰 السعر: {order_data['price']:,} SYP\n"
                    plain_message += f"📅 التاريخ والوقت: {order_data['timestamp']}\n"
                    plain_message += f"📊 الحالة: {order_data['status']}"

                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=plain_message,
                        reply_markup=reply_markup
                    )

                logger.info(f"Admin notification for order {order_id} sent successfully on attempt {attempt + 1}")
                return
            except Exception as e:
                logger.error(f"Failed to notify admin about order {order_id} (attempt {attempt + 1}): {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2)

        # If all attempts failed, log critical error
        logger.critical(f"CRITICAL: Failed to notify admin about order {order_id} after {max_attempts} attempts. Admin ID: {ADMIN_ID}")

    async def send_balance_request_to_channel(self, context: ContextTypes.DEFAULT_TYPE, user, amount: int, transaction_number: str, payment_method: str, reply_markup) -> bool:
        """Send balance request to dedicated channel"""
        try:
            # Create message based on payment method
            if payment_method == 'payeer':
                usd_amount = context.user_data.get('usd_amount', 0)
                message = f"💳 طلب شحن رصيد عبر Payeer\n\n"
                message += f"👤 المستخدم: @{user.username or user.first_name} ({user.id})\n"
                message += f"💱 المبلغ المرسل: {usd_amount} USD\n"
                message += f"💰 القيمة بالليرة: {amount:,} SYP\n"
                message += f"📱 رقم العملية: {transaction_number}\n"
                message += f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                message += f"⏳ الحالة: في انتظار المراجعة"
            elif payment_method == 'usdt_bep20':
                usd_amount = context.user_data.get('usd_amount', 0)
                message = f"💳 طلب شحن رصيد عبر USDT BEP-20\n\n"
                message += f"👤 المستخدم: @{user.username or user.first_name} ({user.id})\n"
                message += f"💱 المبلغ المرسل: {usd_amount} USDT\n"
                message += f"💰 القيمة بالليرة: {amount:,} SYP\n"
                message += f"📱 رقم العملية: {transaction_number}\n"
                message += f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                message += f"⏳ الحالة: في انتظار المراجعة"
            elif payment_method == 'shamcash' and context.user_data.get('shamcash_currency') == 'USD':
                usd_amount = context.user_data.get('usd_amount', 0)
                message = f"💳 طلب شحن رصيد عبر شام كاش (USD)\n\n"
                message += f"👤 المستخدم: @{user.username or user.first_name} ({user.id})\n"
                message += f"💱 المبلغ المرسل: {usd_amount} USD\n"
                message += f"💰 القيمة بالليرة: {amount:,} SYP\n"
                message += f"📱 رقم العملية: {transaction_number}\n"
                message += f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                message += f"⏳ الحالة: في انتظار المراجعة"
            else:
                # For Syriatel and Shamcash (SYP)
                method_display = "شام كاش" if payment_method == 'shamcash' else "سيريتل كاش"
                message = f"💳 طلب شحن رصيد عبر {method_display}\n\n"
                message += f"👤 المستخدم: @{user.username or user.first_name} ({user.id})\n"
                message += f"💰 المبلغ: {amount:,} SYP\n"
                message += f"📱 رقم العملية: {transaction_number}\n"
                message += f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                message += f"⏳ الحالة: في انتظار المراجعة"

            await context.bot.send_message(
                chat_id=BALANCE_REQUESTS_CHANNEL,
                text=message,
                reply_markup=reply_markup
            )
            logger.info(f"Balance request sent to channel {BALANCE_REQUESTS_CHANNEL} successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to send balance request to channel: {e}")
            return False

    async def send_balance_request_to_admin(self, context: ContextTypes.DEFAULT_TYPE, user, amount: int, transaction_number: str, payment_method: str, reply_markup, is_backup: bool = False) -> bool:
        """Send balance request to admin (as backup or monitoring copy)"""
        max_attempts = 4

        for attempt in range(max_attempts):
            try:
                # Create admin message based on payment method
                if payment_method == 'payeer':
                    usd_amount = context.user_data.get('usd_amount', 0)
                    base_message = f"💳 طلب شحن رصيد عبر Payeer\n\n"
                    if is_backup:
                        base_message = f"📋 نسخة مراقبة - " + base_message
                    base_message += f"👤 المستخدم: @{user.username or user.first_name} ({user.id})\n"
                    base_message += f"💱 المبلغ المرسل: {usd_amount} USD\n"
                    base_message += f"💰 القيمة بالليرة: {amount:,} SYP\n"
                    base_message += f"📱 رقم العملية: {transaction_number}\n"
                    base_message += f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                    base_message += f"⏳ الحالة: في انتظار المراجعة"
                elif payment_method == 'usdt_bep20':
                    usd_amount = context.user_data.get('usd_amount', 0)
                    base_message = f"💳 طلب شحن رصيد عبر USDT BEP-20\n\n"
                    if is_backup:
                        base_message = f"📋 نسخة مراقبة - " + base_message
                    base_message += f"👤 المستخدم: @{user.username or user.first_name} ({user.id})\n"
                    base_message += f"💱 المبلغ المرسل: {usd_amount} USDT\n"
                    base_message += f"💰 القيمة بالليرة: {amount:,} SYP\n"
                    base_message += f"📱 رقم العملية: {transaction_number}\n"
                    base_message += f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                    base_message += f"⏳ الحالة: في انتظار المراجعة"
                elif payment_method == 'shamcash' and context.user_data.get('shamcash_currency') == 'USD':
                    usd_amount = context.user_data.get('usd_amount', 0)
                    base_message = f"💳 طلب شحن رصيد عبر شام كاش (USD)\n\n"
                    if is_backup:
                        base_message = f"📋 نسخة مراقبة - " + base_message
                    base_message += f"👤 المستخدم: @{user.username or user.first_name} ({user.id})\n"
                    base_message += f"💱 المبلغ المرسل: {usd_amount} USD\n"
                    base_message += f"💰 القيمة بالليرة: {amount:,} SYP\n"
                    base_message += f"📱 رقم العملية: {transaction_number}\n"
                    base_message += f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                    base_message += f"⏳ الحالة: في انتظار المراجعة"
                else:
                    # For Syriatel and Shamcash (SYP)
                    method_display = "شام كاش" if payment_method == 'shamcash' else "سيريتل كاش"
                    base_message = f"💳 طلب شحن رصيد عبر {method_display}\n\n"
                    if is_backup:
                        base_message = f"📋 نسخة مراقبة - " + base_message
                    base_message += f"👤 المستخدم: @{user.username or user.first_name} ({user.id})\n"
                    base_message += f"💰 المبلغ: {amount:,} SYP\n"
                    base_message += f"📱 رقم العملية: {transaction_number}\n"
                    base_message += f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                    base_message += f"⏳ الحالة: في انتظار المراجعة"

                if attempt == 0:
                    # First attempt with MarkdownV2
                    admin_message = base_message.replace('(', '\\(').replace(')', '\\)').replace('-', '\\-').replace('.', '\\.')
                    admin_message = admin_message.replace('`', '\\`')

                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=admin_message,
                        reply_markup=reply_markup,
                        parse_mode='MarkdownV2'
                    )
                elif attempt == 1:
                    # Second attempt with HTML
                    admin_message = base_message.replace(f"({user.id})", f"(<code>{user.id}</code>)")
                    admin_message = admin_message.replace(f"{transaction_number}", f"<code>{transaction_number}</code>")

                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=admin_message,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                elif attempt == 2:
                    # Third attempt with basic Markdown
                    admin_message = base_message.replace(f"({user.id})", f"(`{user.id}`)")
                    admin_message = admin_message.replace(f"{transaction_number}", f"`{transaction_number}`")

                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=admin_message,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                else:
                    # Fourth attempt without any formatting
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=base_message,
                        reply_markup=reply_markup
                    )

                logger.info(f"Admin notification sent successfully on attempt {attempt + 1}")
                return True
            except Exception as e:
                logger.error(f"Failed to send transfer request to admin (attempt {attempt + 1}): {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2)  # Wait 2 seconds before retry

        # If all attempts failed
        logger.error(f"CRITICAL: Failed to notify admin about payment request after {max_attempts} attempts")
        if not is_backup:
            try:
                await context.bot.send_message(
                    chat_id=user.id,
                    text="⚠️ تم استلام طلبك ولكن حدث خطأ في إرسال الإشعار للإدارة. يرجى التواصل مع الدعم الفني."
                )
            except Exception as e:
                logger.error(f"Failed to notify user about notification failure: {e}")

        return False

    async def handle_admin_order_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin order approval/rejection"""
        query = update.callback_query
        await query.answer()

        if not data_manager.is_user_admin(update.effective_user.id):
            return

        action, order_id = query.data.split('_', 2)[0], query.data.split('_', 2)[2]

        # Get order details
        orders = data_manager._load_json(data_manager.orders_file)
        order = orders.get(order_id)

        if not order:
            await query.edit_message_text("❌ الطلب غير موجود")
            return

        # Get item details for the complete message
        if order['service_type'] == 'app':
            items = data_manager.get_apps()
        else:
            items = data_manager.get_games()

        item_data = items.get(order['item_id'], {})
        category_data = item_data.get('categories', {}).get(order['category_id'], {})

        if action == "approve":
            data_manager.update_order_status(order_id, "مكتمل وتم الشحن بنجاح")

            # Mark user as having made a purchase and check if it's their first
            is_first_purchase = data_manager.mark_user_purchased(order['user_id'])

            # Send congratulations message on first purchase
            if is_first_purchase:
                referral_settings = data_manager.get_referral_settings()
                if referral_settings["enabled"]:
                    try:
                        await context.bot.send_message(
                            chat_id=order['user_id'],
                            text="🎉 **مبروك لقد تم تفعيل نظام الإحالة** 🎉\n\nيمكنك البدء بالكسب من خلال رابط إحالتك ⚡ 🔥\n\nاختر \"نظام الإحالة 🎁\" من القائمة للحصول على رابطك الخاص!",
                            parse_mode='Markdown'
                        )
                    except Exception as e:
                        logger.error(f"Failed to send referral activation message to user {order['user_id']}: {e}")

            # Process referral earnings
            referral_settings = data_manager.get_referral_settings()
            if referral_settings["enabled"]:
                users = data_manager._load_json(data_manager.users_file)
                user_data = users.get(str(order['user_id']))

                if user_data and user_data.get('referred_by'):
                    order_price = order['price']

                    # Level 1 referral earnings (1%)
                    level_1_user_id = user_data['referred_by']
                    level_1_user_data = users.get(str(level_1_user_id))

                    if level_1_user_data:
                        level_1_earnings = order_price * (referral_settings['level_1_percentage'] / 100)

                        if data_manager.add_referral_earnings(level_1_user_id, level_1_earnings, from_user_id=order['user_id'], level=1):
                            # Send notification to level 1 referrer
                            # Get the purchasing user's referral ID
                            purchasing_user_ref_id = user_data.get('referral_id', order['user_id'])

                            try:
                                await context.bot.send_message(
                                    chat_id=level_1_user_id,
                                    text=f"💰 تم إضافة **{level_1_earnings:,.2f} SYP** إلى أرباح الإحالة الخاصة بك من عملية شحن قام بها المستخدم REF_{purchasing_user_ref_id}",
                                    parse_mode='Markdown'
                                )
                            except Exception as e:
                                logger.error(f"Failed to send referral notification to level 1 user {level_1_user_id}: {e}")

                        # Level 2 referral earnings (0.5%)
                        if level_1_user_data.get('referred_by'):
                            level_2_user_id = level_1_user_data['referred_by']
                            level_2_user_data = users.get(str(level_2_user_id))

                            if level_2_user_data:
                                level_2_earnings = order_price * (referral_settings['level_2_percentage'] / 100)

                                if data_manager.add_referral_earnings(level_2_user_id, level_2_earnings, from_user_id=order['user_id'], level=2):
                                    # Send notification to level 2 referrer
                                    # Get the purchasing user's referral ID
                                    purchasing_user_ref_id = user_data.get('referral_id', order['user_id'])

                                    try:
                                        await context.bot.send_message(
                                            chat_id=level_2_user_id,
                                            text=f"💰 تم إضافة **{level_2_earnings:,.2f} SYP** إلى أرباح الإحالة الخاصة بك من عملية شحن قام بها المستخدم REF_{purchasing_user_ref_id} (مستوى ثاني)",
                                            parse_mode='Markdown'
                                        )
                                    except Exception as e:
                                        logger.error(f"Failed to send referral notification to level 2 user {level_2_user_id}: {e}")

            # Update admin message without markdown to avoid parsing errors
            admin_message = f"🔔 طلب جديد\n\n"
            admin_message += f"🆔 رقم الطلب: {order_id}\n"
            admin_message += f"👤 المستخدم: @{order['username']} ({order['user_id']})\n"
            admin_message += f"🎮 الخدمة: {item_data.get('name', 'N/A')}\n"
            admin_message += f"📦 الفئة: {category_data.get('name', 'N/A')}\n"

            if order['quantity'] != 1:
                admin_message += f"📊 الكمية: {order['quantity']}\n"

            admin_message += f"🔑 معرف الحساب: {order['account_id']}\n"
            admin_message += f"💰 السعر: {order['price']:,.2f} SYP\n"
            admin_message += f"📅 التاريخ والوقت: {order['timestamp']}\n"
            admin_message += f"📊 الحالة: مكتمل وتم الشحن بنجاح ✅"

            await query.edit_message_text(admin_message)

            # Send updated message to user
            service_type_name = "شحن تطبيق" if order['service_type'] == 'app' else "شحن لعبة"
            user_message = f"📋 تفاصيل الطلب:\n\n"
            user_message += f"📱 القسم: {service_type_name}\n\n"
            user_message += f"🎮 الخدمة: {item_data.get('name', 'N/A')}\n\n"
            user_message += f"🏷️ الفئة: {category_data.get('name', 'N/A')}\n\n"

            if order['quantity'] != 1:
                user_message += f"📊 الكمية: {order['quantity']}\n\n"

            user_message += f"🔑 معرف الحساب: {order['account_id']}\n\n"
            user_message += f"💰 السعر الإجمالي: {order['price']:,.2f} SYP\n\n"
            user_message += f"🆔 رقم الطلب: {order_id}\n\n"
            user_message += f"🕐 التاريخ والوقت: {order['timestamp']}\n\n"
            user_message += "✅ تم شحن طلبك بنجاح\n\n"
            user_message += "📊 حالة الطلب: مكتمل وتم الشحن بنجاح ✅"

            try:
                await context.bot.send_message(
                    chat_id=order['user_id'],
                    text=user_message
                )
            except Exception as e:
                logger.error(f"Failed to notify user: {e}")

        elif action == "reject":
            # Refund user balance
            data_manager.update_user_balance(order['user_id'], order['price'])
            data_manager.update_order_status(order_id, "مرفوض ولم تكتمل العملية")

            # Update admin message without markdown to avoid parsing errors
            admin_message = f"🔔 طلب جديد\n\n"
            admin_message += f"🆔 رقم الطلب: {order_id}\n"
            admin_message += f"👤 المستخدم: @{order['username']} ({order['user_id']})\n"
            admin_message += f"🎮 الخدمة: {item_data.get('name', 'N/A')}\n"
            admin_message += f"📦 الفئة: {category_data.get('name', 'N/A')}\n"

            if order['quantity'] != 1:
                admin_message += f"📊 الكمية: {order['quantity']}\n"

            admin_message += f"🔑 معرف الحساب: {order['account_id']}\n"
            admin_message += f"💰 السعر: {order['price']:,.2f} SYP\n"
            admin_message += f"📅 التاريخ والوقت: {order['timestamp']}\n"
            admin_message += f"📊 الحالة: مرفوض ولم تكتمل العملية ❌"

            await query.edit_message_text(admin_message)

            # Send updated message to user
            service_type_name = "شحن تطبيق" if order['service_type'] == 'app' else "شحن لعبة"
            user_message = f"📋 تفاصيل الطلب:\n\n"
            user_message += f"📱 القسم: {service_type_name}\n\n"
            user_message += f"🎮 الخدمة: {item_data.get('name', 'N/A')}\n\n"
            user_message += f"🏷️ الفئة: {category_data.get('name', 'N/A')}\n\n"

            if order['quantity'] != 1:
                user_message += f"📊 الكمية: {order['quantity']}\n\n"

            user_message += f"🔑 معرف الحساب: {order['account_id']}\n\n"
            user_message += f"💰 السعر الإجمالي: {order['price']:,.2f} SYP\n\n"
            user_message += f"🆔 رقم الطلب: {order_id}\n\n"
            user_message += f"🕐 التاريخ والوقت: {order['timestamp']}\n\n"
            user_message += "❌ تم رفض طلبك ولم تكتمل العملية\n\n"
            user_message += f"📊 حالة الطلب: مرفوض ولم تكتمل العملية ❌\n\n"
            user_message += f"💰 تم إرجاع {order['price']:,.2f} SYP لرصيدك"

            try:
                await context.bot.send_message(
                    chat_id=order['user_id'],
                    text=user_message
                )
            except Exception as e:
                logger.error(f"Failed to notify user: {e}")

    async def show_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show admin panel"""
        if not data_manager.is_user_admin(update.effective_user.id):
            await update.message.reply_text("غير مسموح لك بالوصول لهذه الخدمة.")
            return MAIN_MENU

        # Get statistics
        pending_orders = data_manager.get_pending_orders()
        all_users = data_manager.get_all_users()
        total_users = len(all_users)
        total_balance = sum(user.get('balance', 0) for user in all_users.values())
        spending_15_days = data_manager.get_spending_last_15_days()

        message = "🛠 **لوحة التحكم**\n\n"
        message += "📊 **الإحصائيات السريعة:**\n\n"
        message += f"📋 الطلبات المعلقة: **{len(pending_orders)}**\n\n"
        message += f"👥 إجمالي المستخدمين: **{total_users:,}**\n\n"
        message += f"💰 إجمالي الأرصدة: **{total_balance:,} SYP**\n\n"
        message += f"💸 إنفاق المستخدمين (آخر 15 يوم): **{spending_15_days:,} SYP**\n\n"
        message += "──────────────────────────\n\n"
        message += "اختر العملية المطلوبة:"

        keyboard = [
            [KeyboardButton("إدارة التطبيقات والألعاب 📱🎮")],
            [KeyboardButton("إدارة المستخدمين 👥"), KeyboardButton("الإحصائيات 📊")],
            [KeyboardButton("إدارة الأدمن 🔑"), KeyboardButton("إعدادات الإحالة 🎁")],
            [KeyboardButton("إضافة رصيد لمستخدم 💰")],
            [KeyboardButton("تعيين حساب الدعم 👨‍💻")],
            [KeyboardButton("إدارة عناوين الدفع 🏦"), KeyboardButton("إدارة أكواد الشحن 🏷️")],
            [KeyboardButton("تعديل أسعار جماعي 📈"), KeyboardButton("إذاعة عامة 📢")],
            [KeyboardButton("إعدادات البوت ⚙️"), KeyboardButton("اختبار الإشعارات 🔔")],
            [KeyboardButton("⬅️ العودة للقائمة الرئيسية")]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return ADMIN_PANEL

    async def handle_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle admin panel actions"""
        text = update.message.text

        if text == "إدارة التطبيقات والألعاب 📱🎮":
            return await self.show_apps_management(update, context)

        elif text == "إضافة رصيد لمستخدم 💰":
            await update.message.reply_text("أرسل معرف المستخدم والمبلغ بالصيغة التالية:\n\nuser_id amount\n\nمثال: 123456789 5000")
            return ADD_BALANCE

        elif text == "تعيين حساب الدعم 👨‍💻":
            current_support = data_manager.get_support_username()
            if current_support:
                message = f"حساب الدعم الحالي: @{current_support}\n\n"
            else:
                message = "لم يتم تعيين حساب دعم بعد.\n\n"
            message += "أرسل اسم المستخدم الجديد للدعم (بدون @):"
            await update.message.reply_text(message)
            return SETTING_SUPPORT_USERNAME

        elif text == "إدارة عناوين الدفع 🏦":
            return await self.show_payment_addresses_management(update, context)

        elif text == "إدارة أكواد الشحن 🏷️":
            return await self.show_charge_codes_management(update, context)

        elif text == "إذاعة عامة 📢":
            await update.message.reply_text(
                "أرسل الرسالة التي تريد إذاعتها لجميع مستخدمي البوت:",
                reply_markup=ReplyKeyboardRemove()
            )
            return ENTERING_BROADCAST_MESSAGE

        elif text == "إعدادات البوت ⚙️":
            return await self.show_bot_settings(update, context)

        elif text == "إدارة المستخدمين 👥":
            return await self.show_user_management(update, context)

        elif text == "الإحصائيات 📊":
            return await self.show_statistics(update, context)

        elif text == "إدارة الأدمن 🔑":
            return await self.show_admins_management(update, context)

        elif text == "إعدادات الإحالة 🎁":
            return await self.show_referral_management(update, context)

        elif text == "تعديل أسعار جماعي 📈":
            return await self.show_bulk_price_adjustment(update, context)

        elif text == "اختبار الإشعارات 🔔":
            # Test notifications to all channels
            await update.message.reply_text("⏳ جاري اختبار نظام الإشعارات...")

            test_message = f"🔔 **اختبار نظام الإشعارات**\n\n"
            test_message += f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            test_message += f"✅ نظام إشعارات القنوات يعمل بشكل صحيح!"

            channels_status = []

            # Test orders channel
            try:
                await context.bot.send_message(
                    chat_id=ORDERS_CHANNEL,
                    text=test_message,
                    parse_mode='Markdown'
                )
                channels_status.append("✅ قناة الطلبات")
            except Exception as e:
                channels_status.append(f"❌ قناة الطلبات: {str(e)[:50]}")
                logger.error(f"Test notification to orders channel failed: {e}")

            await asyncio.sleep(0.3)

            # Test balance requests channel
            try:
                await context.bot.send_message(
                    chat_id=BALANCE_REQUESTS_CHANNEL,
                    text=test_message,
                    parse_mode='Markdown'
                )
                channels_status.append("✅ قناة طلبات الرصيد")
            except Exception as e:
                channels_status.append(f"❌ قناة طلبات الرصيد: {str(e)[:50]}")
                logger.error(f"Test notification to balance requests channel failed: {e}")

            await asyncio.sleep(0.3)

            # Test new users channel
            try:
                await context.bot.send_message(
                    chat_id=NEW_USER_CHANNEL,
                    text=test_message,
                    parse_mode='Markdown'
                )
                channels_status.append("✅ قناة المستخدمين الجدد")
            except Exception as e:
                channels_status.append(f"❌ قناة المستخدمين الجدد: {str(e)[:50]}")
                logger.error(f"Test notification to new users channel failed: {e}")

            # Send report to admin
            report = "📊 **تقرير اختبار الإشعارات:**\n\n"
            report += "\n".join(channels_status)

            await update.message.reply_text(report, parse_mode='Markdown')
            return ADMIN_PANEL

        elif text == "⬅️ العودة للقائمة الرئيسية":
            return await self.start(update, context)

        return ADMIN_PANEL

    async def show_admg01c_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show ADMG01C panel for bot branding"""
        if update.effective_user.id != ADMG01C:
            await update.message.reply_text("غير مسموح لك بالوصول لهذه الخدمة.")
            return MAIN_MENU

        current_name = data_manager.get_bot_name(english=False)
        admins_count = len(data_manager.get_admins())

        message = f"⚙️ **لوحة ADMG01C**\n\n"
        message += f"الاسم الحالي: {current_name}\n"
        message += f"عدد الأدمن: {admins_count}\n\n"
        message += "اختر العملية المطلوبة:"

        keyboard = [
            [KeyboardButton("تغيير اسم البوت 🏷️")],
            [KeyboardButton("إدارة الأدمن 👥")],
            [KeyboardButton("إرسال تحذير للأدمن ⚠️")],
            [KeyboardButton("⬅️ العودة للقائمة الرئيسية")]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return ADMG01C_PANEL

    async def handle_admg01c_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle ADMG01C panel actions"""
        text = update.message.text

        if text == "تغيير اسم البوت 🏷️":
            await update.message.reply_text(
                "أرسل الاسم الجديد للبوت:\n\n"
                "مثال:\n"
                "Azzo Store\n\n"
                "سيتم استبدال الاسم في جميع أنحاء البوت.",
                reply_markup=ReplyKeyboardRemove()
            )
            return ENTERING_NEW_BOT_NAME

        elif text == "إدارة الأدمن 👥":
            return await self.show_admins_management_admg01c(update, context)

        elif text == "إرسال تحذير للأدمن ⚠️":
            message = "⚠️ **تحذير انتهاء الاشتراك**\n\n"
            message += "سيتم إرسال الرسالة التالية لجميع الأدمن:\n\n"
            message += "━━━━━━━━━━━━━━━━━━━━━━\n"
            message += "⚠️ شارف الإشتراك على الإنتهاء تواصل مع الأدمن لتجديد الإشتراك\n"
            message += "وتجنب توقف البوت 🤖\n\n"
            message += "❌ تم إلغاء الخطة PRO plan 📊\n"
            message += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            message += "هل تريد المتابعة؟"

            keyboard = [
                [InlineKeyboardButton("✅ إرسال للأدمن", callback_data="confirm_admins_warning")],
                [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_admins_warning")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            return ADMG01C_PANEL

        elif text == "⬅️ العودة للقائمة الرئيسية":
            return await self.start(update, context)

        return ADMG01C_PANEL

    async def handle_new_bot_name_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle new bot name entry"""
        new_name = update.message.text.strip()

        if not new_name:
            await update.message.reply_text("❌ لا يمكن ترك الاسم فارغاً!")
            return ENTERING_NEW_BOT_NAME

        context.user_data['new_bot_name'] = new_name

        old_name = data_manager.get_bot_name(english=False)

        message = f"📋 **تأكيد التغيير**\n\n"
        message += f"الاسم القديم: {old_name}\n"
        message += f"الاسم الجديد: {new_name}\n\n"
        message += "⚠️ **تحذير**: سيتم استبدال جميع النصوص التي تحتوي على الاسم القديم في البوت.\n\n"
        message += "هل تريد المتابعة؟"

        keyboard = [
            [InlineKeyboardButton("✅ تأكيد التغيير", callback_data="confirm_bot_name_change")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_bot_name_change")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return CONFIRMING_BOT_NAME_CHANGE

    async def handle_bot_name_change_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle bot name change confirmation"""
        query = update.callback_query
        await query.answer()

        if query.data == "cancel_bot_name_change":
            await query.edit_message_text("❌ تم إلغاء تغيير اسم البوت.")
            context.user_data.clear()
            return MAIN_MENU

        elif query.data == "confirm_bot_name_change":
            new_name = context.user_data.get('new_bot_name')

            try:
                data_manager.set_bot_name(new_name, new_name)

                await query.edit_message_text(
                    f"✅ تم تغيير اسم البوت بنجاح!\n\n"
                    f"الاسم الجديد: {new_name}\n\n"
                    f"ملاحظة: الاسم الجديد سيظهر في الرسائل الجديدة."
                )

                logger.info(f"Bot name changed to: {new_name}")

            except Exception as e:
                logger.error(f"Error changing bot name: {e}")
                await query.edit_message_text(f"❌ حدث خطأ في تغيير اسم البوت: {str(e)}")

            context.user_data.clear()
            return MAIN_MENU

        return MAIN_MENU

    async def show_admins_management_admg01c(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show admins management panel"""
        admins = data_manager.get_admins()

        message = "👥 **إدارة الأدمن**\n\n"

        if admins:
            message += "📋 **قائمة الأدمن الحاليين:**\n\n"
            for admin_id, admin_data in admins.items():
                created_date = datetime.fromisoformat(admin_data['created_at']).strftime('%Y-%m-%d')
                message += f"• {admin_data['name']}\n"
                message += f"  🆔 {admin_data['user_id']}\n"
                message += f"  📅 {created_date}\n\n"
        else:
            message += "لا يوجد أدمن مضافين حالياً.\n\n"

        message += "اختر العملية:"

        keyboard = [
            [KeyboardButton("إضافة أدمن جديد ➕")],
            [KeyboardButton("حذف أدمن ❌")] if admins else [],
            [KeyboardButton("⬅️ العودة لـ ADMG01C")]
        ]

        keyboard = [row for row in keyboard if row]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return MANAGING_ADMINS_ADMG01C

    async def handle_admins_management_admg01c(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle admins management actions"""
        text = update.message.text

        if text == "إضافة أدمن جديد ➕":
            await update.message.reply_text(
                "أرسل معرف المستخدم (User ID) للأدمن الجديد:",
                reply_markup=ReplyKeyboardRemove()
            )
            return ENTERING_ADMIN_USER_ID_ADMG01C

        elif text == "حذف أدمن ❌":
            admins = data_manager.get_admins()

            if not admins:
                await update.message.reply_text("لا يوجد أدمن لحذفهم.")
                return MANAGING_ADMINS_ADMG01C

            keyboard = []
            for admin_id, admin_data in admins.items():
                keyboard.append([KeyboardButton(f"{admin_data['name']} - {admin_data['user_id']}")])

            keyboard.append([KeyboardButton("⬅️ العودة")])

            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(
                "اختر الأدمن المراد حذفه:",
                reply_markup=reply_markup
            )
            return SELECTING_ADMIN_TO_DELETE_ADMG01C

        elif text == "⬅️ العودة لـ ADMG01C":
            return await self.show_admg01c_panel(update, context)

        return MANAGING_ADMINS_ADMG01C

    async def handle_admin_user_id_entry_admg01c(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle admin user ID entry"""
        try:
            user_id = int(update.message.text.strip())

            if user_id == ADMIN_ID or user_id == ADMG01C:
                await update.message.reply_text(
                    "❌ هذا المستخدم هو أدمن رئيسي بالفعل."
                )
                return ENTERING_ADMIN_USER_ID_ADMG01C

            if data_manager.is_user_admin(user_id):
                await update.message.reply_text(
                    "❌ هذا المستخدم هو أدمن بالفعل."
                )
                return ENTERING_ADMIN_USER_ID_ADMG01C

            context.user_data['new_admin_user_id'] = user_id

            await update.message.reply_text(
                "أرسل اسم الأدمن:"
            )
            return ADDING_ADMIN_ADMG01C

        except ValueError:
            await update.message.reply_text(
                "❌ معرف غير صحيح! يرجى إرسال رقم صحيح."
            )
            return ENTERING_ADMIN_USER_ID_ADMG01C

    async def handle_admin_name_entry_admg01c(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle admin name entry"""
        admin_name = update.message.text.strip()

        if not admin_name:
            await update.message.reply_text("❌ لا يمكن ترك الاسم فارغاً!")
            return ADDING_ADMIN_ADMG01C

        user_id = context.user_data.get('new_admin_user_id')

        message = f"📋 **تأكيد إضافة أدمن**\n\n"
        message += f"الاسم: {admin_name}\n"
        message += f"معرف المستخدم: {user_id}\n\n"
        message += "هل تريد المتابعة؟"

        keyboard = [
            [InlineKeyboardButton("✅ تأكيد الإضافة", callback_data=f"confirm_add_admin_{user_id}_{admin_name}")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_admin_admg01c")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return CONFIRMING_ADMIN_ADD_ADMG01C

    async def handle_admin_selection_for_delete_admg01c(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle admin selection for deletion"""
        text = update.message.text

        if text == "⬅️ العودة":
            return await self.show_admins_management_admg01c(update, context)

        admins = data_manager.get_admins()
        selected_admin_id = None

        for admin_id, admin_data in admins.items():
            expected_text = f"{admin_data['name']} - {admin_data['user_id']}"
            if text == expected_text:
                selected_admin_id = admin_id
                context.user_data['admin_to_delete'] = admin_id
                break

        if not selected_admin_id:
            await update.message.reply_text("يرجى اختيار أدمن من القائمة.")
            return SELECTING_ADMIN_TO_DELETE_ADMG01C

        admin_data = admins[selected_admin_id]

        message = f"⚠️ **تأكيد حذف الأدمن**\n\n"
        message += f"الاسم: {admin_data['name']}\n"
        message += f"المعرف: {admin_data['user_id']}\n\n"
        message += "هل أنت متأكد من حذف هذا الأدمن؟"

        keyboard = [
            [InlineKeyboardButton("✅ حذف الأدمن", callback_data=f"confirm_delete_admin_{selected_admin_id}")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_delete_admin_admg01c")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return CONFIRMING_ADMIN_DELETE_ADMG01C

    async def handle_admin_callbacks_admg01c(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle admin management callbacks"""
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "confirm_admins_warning":
            # Show initial processing message
            try:
                await query.edit_message_text("⏳ جاري إرسال التحذير للأدمن...\n\nيرجى الانتظار...")
            except Exception as e:
                logger.error(f"Failed to update initial message: {e}")

            warning_message = (
                "⚠️ شارف الإشتراك على الإنتهاء تواصل مع الأدمن لتجديد الإشتراك\n"
                "وتجنب توقف البوت 🤖\n\n"
                "❌ تم إلغاء الخطة PRO plan 📊"
            )

            success_count = 0
            failed_count = 0
            sent_to = []
            failed_to = []

            # Send to main admin (ADMIN_ID)
            if ADMIN_ID > 0:
                try:
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=warning_message
                    )
                    success_count += 1
                    sent_to.append(f"الأدمن الرئيسي ({ADMIN_ID})")
                    logger.info(f"Warning sent successfully to main admin {ADMIN_ID}")
                except Exception as e:
                    logger.error(f"Failed to send warning to main admin {ADMIN_ID}: {e}")
                    failed_count += 1
                    failed_to.append(f"الأدمن الرئيسي ({ADMIN_ID}): {str(e)[:50]}")

                await asyncio.sleep(0.3)

            # Send to ADMG01C if exists and different from main admin
            if ADMG01C > 0 and ADMG01C != ADMIN_ID:
                try:
                    await context.bot.send_message(
                        chat_id=ADMG01C,
                        text=warning_message
                    )
                    success_count += 1
                    sent_to.append(f"ADMG01C ({ADMG01C})")
                    logger.info(f"Warning sent successfully to ADMG01C {ADMG01C}")
                except Exception as e:
                    logger.error(f"Failed to send warning to ADMG01C {ADMG01C}: {e}")
                    failed_count += 1
                    failed_to.append(f"ADMG01C ({ADMG01C}): {str(e)[:50]}")

                await asyncio.sleep(0.3)

            # Get all registered admins from data_manager
            try:
                admins = data_manager.get_admins()
                logger.info(f"Found {len(admins)} registered admins in database")

                # Send to all registered admins
                for admin_id, admin_data in admins.items():
                    admin_user_id = admin_data.get('user_id')
                    admin_name = admin_data.get('name', 'غير محدد')

                    if not admin_user_id:
                        logger.warning(f"Skipping admin {admin_name} - no user_id")
                        continue

                    logger.info(f"Processing admin: {admin_name} (ID: {admin_user_id})")

                    # Skip if same as ADMIN_ID or ADMG01C (already sent)
                    if admin_user_id == ADMIN_ID or admin_user_id == ADMG01C:
                        logger.info(f"Skipping {admin_name} - already sent as main admin or ADMG01C")
                        continue

                    try:
                        await context.bot.send_message(
                            chat_id=admin_user_id,
                            text=warning_message
                        )
                        success_count += 1
                        sent_to.append(f"{admin_name} ({admin_user_id})")
                        logger.info(f"Warning sent successfully to admin {admin_name} ({admin_user_id})")
                    except Exception as e:
                        logger.error(f"Failed to send warning to admin {admin_name} ({admin_user_id}): {e}")
                        failed_count += 1
                        failed_to.append(f"{admin_name} ({admin_user_id}): {str(e)[:50]}")

                    await asyncio.sleep(0.3)

            except Exception as e:
                logger.error(f"Error getting admins list: {e}")
                failed_count += 1
                failed_to.append(f"خطأ في جلب قائمة الأدمن: {str(e)[:50]}")

            # Build detailed report
            report_message = "📊 **تقرير إرسال التحذير**\n\n"
            report_message += f"━━━━━━━━━━━━━━━━━━━━━━\n"
            report_message += f"✅ نجح: {success_count}\n"
            report_message += f"❌ فشل: {failed_count}\n"
            report_message += f"📈 الإجمالي: {success_count + failed_count}\n"
            report_message += f"━━━━━━━━━━━━━━━━━━━━━━\n\n"

            if sent_to:
                report_message += "✅ **تم الإرسال بنجاح إلى:**\n"
                for recipient in sent_to:
                    report_message += f"• {recipient}\n"
                report_message += "\n"

            if failed_to:
                report_message += "❌ **فشل الإرسال إلى:**\n"
                for recipient in failed_to:
                    report_message += f"• {recipient}\n"
                report_message += "\n"

            if not sent_to and not failed_to:
                report_message += "⚠️ **تنبيه:**\n"
                report_message += "• لم يتم العثور على أدمن في النظام\n"
                report_message += "• يرجى إضافة أدمن أولاً من خلال 'إدارة الأدمن'\n"

            report_message += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            # Send the final report
            try:
                await query.edit_message_text(report_message, parse_mode='Markdown')
                logger.info("Report sent successfully")
            except Exception as e:
                logger.error(f"Failed to edit message with report: {e}")
                # Try sending as new message if edit fails
                try:
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=report_message,
                        parse_mode='Markdown'
                    )
                    logger.info("Report sent as new message")
                except Exception as e2:
                    logger.error(f"Failed to send report as new message: {e2}")
                    # Last resort: send without markdown
                    try:
                        await context.bot.send_message(
                            chat_id=query.message.chat_id,
                            text=report_message.replace('**', '').replace('`', '')
                        )
                    except Exception as e3:
                        logger.error(f"All attempts to send report failed: {e3}")

            return ADMG01C_PANEL

        elif data == "cancel_admins_warning":
            await query.edit_message_text("❌ تم إلغاء إرسال التحذير.")
            return ADMG01C_PANEL

        elif data.startswith("confirm_add_admin_"):
            parts = data.replace("confirm_add_admin_", "").split("_", 1)
            user_id = int(parts[0])
            admin_name = parts[1] if len(parts) > 1 else "مسؤول جديد"

            try:
                data_manager.add_admin(user_id, admin_name)
                await query.edit_message_text(
                    f"✅ تم إضافة الأدمن '{admin_name}' بنجاح!\n\n"
                    f"معرف المستخدم: {user_id}"
                )

                try:
                    bot_name = data_manager.get_bot_name(english=False)
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"🎉 تهانينا! تم تعيينك كمسؤول في بوت {bot_name}\n\n"
                             f"لديك الآن صلاحيات الإدارة في البوت."
                    )
                except Exception as e:
                    logger.error(f"Failed to notify new admin: {e}")

            except Exception as e:
                logger.error(f"Error adding admin: {e}")
                await query.edit_message_text(f"❌ حدث خطأ في إضافة الأدمن: {str(e)}")

            context.user_data.clear()
            return MANAGING_ADMINS_ADMG01C

        elif data == "cancel_add_admin_admg01c":
            await query.edit_message_text("❌ تم إلغاء إضافة الأدمن.")
            context.user_data.clear()
            return MANAGING_ADMINS_ADMG01C

        elif data.startswith("confirm_delete_admin_"):
            admin_id = data.replace("confirm_delete_admin_", "")

            try:
                admins = data_manager.get_admins()
                if admin_id in admins:
                    admin_data = admins[admin_id]
                    success = data_manager.delete_admin(admin_id)

                    if success:
                        await query.edit_message_text(
                            f"✅ تم حذف الأدمن '{admin_data['name']}' بنجاح!"
                        )

                        try:
                            bot_name = data_manager.get_bot_name(english=False)
                            await context.bot.send_message(
                                chat_id=admin_data['user_id'],
                                text=f"📢 تم إلغاء تعيينك كمسؤول في بوت {bot_name}"
                            )
                        except:
                            pass
                    else:
                        await query.edit_message_text("❌ فشل في حذف الأدمن.")
                else:
                    await query.edit_message_text("❌ الأدمن غير موجود.")
            except Exception as e:
                logger.error(f"Error deleting admin: {e}")
                await query.edit_message_text(f"❌ حدث خطأ في حذف الأدمن: {str(e)}")

            context.user_data.clear()
            return MANAGING_ADMINS_ADMG01C

        elif data == "cancel_delete_admin_admg01c":
            await query.edit_message_text("❌ تم إلغاء حذف الأدمن.")
            context.user_data.clear()
            return MANAGING_ADMINS_ADMG01C

        return MANAGING_ADMINS_ADMG01C

    async def promote_demote_channel_admin(self, context: ContextTypes.DEFAULT_TYPE, user_id: int, promote: bool = True):
        """Promote or demote user in all bot channels"""
        channels = [
            {"id": ORDERS_CHANNEL, "name": "قناة الطلبات"},
            {"id": BALANCE_REQUESTS_CHANNEL, "name": "قناة طلبات الرصيد"},
            {"id": NEW_USER_CHANNEL, "name": "قناة المستخدمين"}
        ]
        results = []
        detailed_results = []

        for channel in channels:
            channel_id = channel["id"]
            channel_name = channel["name"]

            try:
                # First check if user is a member
                try:
                    member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
                    is_member = member.status in ['member', 'administrator', 'creator', 'restricted']
                except Exception as e:
                    is_member = False
                    logger.warning(f"Could not check membership for user {user_id} in {channel_name}: {e}")

                if not is_member:
                    results.append(f"⚠️ ليس عضواً")
                    detailed_results.append(f"• {channel_name}: المستخدم ليس عضواً في القناة")
                    continue

                if promote:
                    # Promote user to admin in channel
                    await context.bot.promote_chat_member(
                        chat_id=channel_id,
                        user_id=user_id,
                        can_manage_chat=False,
                        can_post_messages=True,
                        can_edit_messages=True,
                        can_delete_messages=True,
                        can_manage_video_chats=False,
                        can_restrict_members=False,
                        can_promote_members=False,
                        can_change_info=False,
                        can_invite_users=True,
                        can_pin_messages=True
                    )
                    results.append(f"✅ تمت الإضافة")
                    detailed_results.append(f"• {channel_name}: تمت إضافته كمشرف")
                    logger.info(f"Promoted user {user_id} in channel {channel_id}")
                else:
                    # Demote user (remove admin rights)
                    await context.bot.promote_chat_member(
                        chat_id=channel_id,
                        user_id=user_id,
                        can_manage_chat=False,
                        can_post_messages=False,
                        can_edit_messages=False,
                        can_delete_messages=False,
                        can_manage_video_chats=False,
                        can_restrict_members=False,
                        can_promote_members=False,
                        can_change_info=False,
                        can_invite_users=False,
                        can_pin_messages=False
                    )
                    results.append(f"✅ تمت الإزالة")
                    detailed_results.append(f"• {channel_name}: تم سحب صلاحياته")
                    logger.info(f"Demoted user {user_id} in channel {channel_id}")
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error managing admin in channel {channel_id}: {error_msg}")

                if "CHAT_ADMIN_REQUIRED" in error_msg or "Chat_admin_invite_required" in error_msg:
                    results.append(f"⚠️ صلاحيات غير كافية")
                    detailed_results.append(f"• {channel_name}: البوت يحتاج صلاحية إضافة مشرفين")
                elif "USER_NOT_PARTICIPANT" in error_msg or "Participant_id_invalid" in error_msg:
                    results.append(f"⚠️ ليس عضواً")
                    detailed_results.append(f"• {channel_name}: المستخدم ليس عضواً في القناة")
                else:
                    results.append(f"❌ خطأ")
                    detailed_results.append(f"• {channel_name}: {error_msg}")

        return results, detailed_results

    async def show_admins_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show admins management panel for main admin panel"""
        admins = data_manager.get_admins()

        message = "👥 **إدارة المشرفين**\n\n"
        message += f"🔑 المشرف الرئيسي: {ADMIN_ID}\n\n"

        if admins:
            message += "📋 **قائمة المشرفين الحاليين:**\n\n"
            for admin_id, admin_data in admins.items():
                created_date = datetime.fromisoformat(admin_data['created_at']).strftime('%Y-%m-%d')
                message += f"• {admin_data['name']}\n"
                message += f"  🆔 {admin_data['user_id']}\n"
                message += f"  📅 {created_date}\n\n"
        else:
            message += "لا يوجد مشرفين مضافين حالياً.\n\n"

        message += "اختر العملية:"

        keyboard = [
            [KeyboardButton("إضافة مشرف جديد ➕")],
            [KeyboardButton("حذف مشرف ❌")] if admins else [],
            [KeyboardButton("⬅️ العودة للوحة التحكم")]
        ]

        keyboard = [row for row in keyboard if row]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return MANAGING_ADMINS

    async def show_referral_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show comprehensive referral management panel"""
        referral_settings = data_manager.get_referral_settings()
        settings = data_manager._load_json(data_manager.settings_file)
        show_button = settings.get("show_referral_button", True)

        # Get total referral statistics
        all_users = data_manager.get_all_users()
        total_referral_earnings = sum(user.get('referral_earnings', 0) for user in all_users.values())
        total_withdrawn = sum(user.get('total_referral_earnings', 0) - user.get('referral_earnings', 0) for user in all_users.values())
        total_users_with_referrals = sum(1 for user in all_users.values() if len(user.get('referrals_level_1', [])) > 0)
        total_referrals = sum(len(user.get('referrals_level_1', [])) for user in all_users.values())
        total_active_referrals = sum(1 for user in all_users.values() if user.get('has_purchased', False) and user.get('referred_by'))

        message = "🎁 **إدارة نظام الإحالة**\n\n"
        message += f"📊 حالة النظام: {'مفعل ✅' if referral_settings['enabled'] else 'معطل ❌'}\n"
        message += f"👁️ زر الإحالة في القائمة: {'ظاهر ✅' if show_button else 'مخفي ❌'}\n\n"

        message += "💰 **نسب العمولة:**\n"
        message += f"• المستوى الأول: **{referral_settings['level_1_percentage']}%**\n"
        message += f"• المستوى الثاني: **{referral_settings['level_2_percentage']}%**\n\n"

        message += "══════════════════════════\n\n"
        message += "📈 **إحصائيات شاملة:**\n\n"
        message += f"👥 مستخدمين لديهم إحالات: **{total_users_with_referrals:,}**\n"
        message += f"🔗 إجمالي الإحالات: **{total_referrals:,}**\n"
        message += f"⚡ إحالات فعالة (لديهم مشتريات): **{total_active_referrals:,}**\n"
        message += f"💸 أرباح معلقة: **{total_referral_earnings:,.2f} SYP**\n"
        message += f"✅ أرباح تم سحبها: **{total_withdrawn:,.2f} SYP**\n"
        message += f"💎 إجمالي الأرباح: **{total_referral_earnings + total_withdrawn:,.2f} SYP**\n\n"

        message += "اختر العملية المطلوبة:"

        keyboard = [
            [KeyboardButton("عرض أفضل 10 محيلين 🏆")],
            [KeyboardButton("تفعيل/تعطيل النظام 🔄"), KeyboardButton("إظهار/إخفاء الزر 👁️")],
            [KeyboardButton("تعديل النسب 💰"), KeyboardButton("سجلات المعاملات 📋")],
            [KeyboardButton("إدارة مستخدم 👤")],
            [KeyboardButton("⬅️ العودة للوحة التحكم")]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return MANAGING_REFERRALS

    async def handle_referral_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        text = update.message.text

        if text == "عرض أفضل 10 محيلين 🏆":
            return await self.show_top_referrers(update, context)

        elif text == "تفعيل/تعطيل النظام 🔄":
            return await self.toggle_referral_system(update, context)

        elif text == "إظهار/إخفاء الزر 👁️":
            return await self.toggle_referral_button_visibility(update, context)

        elif text == "تعديل النسب 💰":
            return await self.show_edit_referral_rates(update, context)

        elif text == "سجلات المعاملات 📋":
            return await self.show_referral_transactions_log(update, context)

        elif text == "إدارة مستخدم 👤":
            await update.message.reply_text(
                "أرسل معرف المستخدم (User ID) أو رقم الإحالة:",
                reply_markup=ReplyKeyboardRemove()
            )
            return ENTERING_REFERRAL_USER_ID

        elif text == "⬅️ العودة للوحة التحكم":
            return await self.show_admin_panel(update, context)

        return MANAGING_REFERRALS

    async def show_top_referrers(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        all_users = data_manager.get_all_users()

        user_referrals = []
        for user_id, user_data in all_users.items():
            referrals_count = len(user_data.get('referrals_level_1', []))
            if referrals_count > 0:
                active_count = 0
                for ref_id in user_data.get('referrals_level_1', []):
                    ref_user = all_users.get(str(ref_id))
                    if ref_user and ref_user.get('has_purchased', False):
                        active_count += 1

                user_referrals.append({
                    'user_id': int(user_id),
                    'referral_id': user_data.get('referral_id', 0),
                    'total_count': referrals_count,
                    'active_count': active_count,
                    'earnings': user_data.get('referral_earnings', 0),
                    'total_earnings': user_data.get('total_referral_earnings', 0)
                })

        user_referrals.sort(key=lambda x: x['total_count'], reverse=True)
        top_10 = user_referrals[:10]

        if not top_10:
            message = "🏆 **أفضل 10 محيلين**\n\n"
            message += "لا توجد إحالات حالياً.\n\n"
        else:
            message = "🏆 **أفضل 10 محيلين**\n\n"
            for i, user in enumerate(top_10, 1):
                badge = data_manager.get_referral_badge(user['user_id'])
                message += f"{i}. **REF_{user['referral_id']}** {badge}\n"
                message += f"   🆔 User ID: `{user['user_id']}`\n"
                message += f"   👥 إحالات: {user['total_count']} ({user['active_count']} فعال)\n"
                message += f"   💰 أرباح: {user['total_earnings']:,.2f} SYP\n\n"

        keyboard = [[KeyboardButton("⬅️ العودة لإدارة الإحالات")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return VIEWING_TOP_REFERRERS

    async def toggle_referral_system(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        referral_settings = data_manager.get_referral_settings()
        current_status = referral_settings["enabled"]
        new_status = not current_status

        data_manager.set_referral_settings(enabled=new_status)

        status_text = "مفعل ✅" if new_status else "معطل ❌"
        await update.message.reply_text(
            f"✅ تم تغيير حالة نظام الإحالة بنجاح!\n\nالحالة الجديدة: {status_text}",
            parse_mode='Markdown'
        )

        return await self.show_referral_management(update, context)

    async def toggle_referral_button_visibility(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        settings = data_manager._load_json(data_manager.settings_file)
        current_visibility = settings.get("show_referral_button", True)
        new_visibility = not current_visibility

        settings["show_referral_button"] = new_visibility
        data_manager._save_json(data_manager.settings_file, settings)

        visibility_text = "ظاهر ✅" if new_visibility else "مخفي ❌"
        await update.message.reply_text(
            f"✅ تم تغيير حالة زر الإحالة بنجاح!\n\nالحالة الجديدة: {visibility_text}",
            parse_mode='Markdown'
        )

        return await self.show_referral_management(update, context)

    async def show_edit_referral_rates(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        referral_settings = data_manager.get_referral_settings()

        message = "💰 **تعديل نسب الإحالة**\n\n"
        message += f"النسب الحالية:\n"
        message += f"• المستوى الأول: **{referral_settings['level_1_percentage']}%**\n"
        message += f"• المستوى الثاني: **{referral_settings['level_2_percentage']}%**\n\n"
        message += "أرسل النسب الجديدة بالصيغة التالية:\n"
        message += "`نسبة_المستوى_الأول نسبة_المستوى_الثاني`\n\n"
        message += "مثال: `1.5 0.75`"

        keyboard = [[KeyboardButton("⬅️ إلغاء")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return ENTERING_REFERRAL_RATES

    async def show_referral_transactions_log(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        transactions = data_manager.get_all_referral_transactions(limit=20)

        if not transactions:
            message = "📋 **سجلات معاملات الإحالة**\n\n"
            message += "لا توجد معاملات حالياً.\n\n"
        else:
            message = "📋 **سجلات معاملات الإحالة**\n"
            message += f"(آخر 20 معاملة)\n\n"

            for trans in transactions:
                trans_type = "➕ ربح" if trans['type'] == 'earning' else "➖ سحب"
                message += f"{trans_type} | {trans['timestamp']}\n"
                message += f"🆔 User: `{trans['user_id']}`\n"
                message += f"💰 المبلغ: {trans['amount']:,.2f} SYP\n"
                if trans.get('level'):
                    message += f"📊 المستوى: {trans['level']}\n"
                message += f"📝 {trans['description']}\n\n"

        keyboard = [[KeyboardButton("⬅️ العودة لإدارة الإحالات")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return VIEWING_REFERRAL_TRANSACTIONS

    async def handle_admins_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle admins management actions"""
        text = update.message.text

        if text == "إضافة مشرف جديد ➕":
            await update.message.reply_text(
                "أرسل معرف المستخدم (User ID) للمشرف الجديد:",
                reply_markup=ReplyKeyboardRemove()
            )
            return ENTERING_ADMIN_USER_ID

        elif text == "حذف مشرف ❌":
            admins = data_manager.get_admins()

            if not admins:
                await update.message.reply_text("لا يوجد مشرفين لحذفهم.")
                return MANAGING_ADMINS

            keyboard = []
            for admin_id, admin_data in admins.items():
                keyboard.append([KeyboardButton(f"{admin_data['name']} - {admin_data['user_id']}")])

            keyboard.append([KeyboardButton("⬅️ العودة")])

            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(
                "اختر المشرف المراد حذفه:",
                reply_markup=reply_markup
            )
            return SELECTING_ADMIN_TO_DELETE

        elif text == "⬅️ العودة للوحة التحكم":
            return await self.show_admin_panel(update, context)

        return MANAGING_ADMINS

    async def handle_admin_user_id_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle admin user ID entry"""
        try:
            user_id = int(update.message.text.strip())

            if user_id == ADMIN_ID:
                await update.message.reply_text(
                    "❌ هذا المستخدم هو المشرف الرئيسي بالفعل ولا يمكن إضافته."
                )
                return ENTERING_ADMIN_USER_ID

            if user_id == ADMG01C:
                await update.message.reply_text(
                    "❌ هذا المستخدم هو ADMG01C ولا يمكن إضافته."
                )
                return ENTERING_ADMIN_USER_ID

            if data_manager.is_user_admin(user_id):
                await update.message.reply_text(
                    "❌ هذا المستخدم هو مشرف بالفعل."
                )
                return ENTERING_ADMIN_USER_ID

            context.user_data['new_admin_user_id'] = user_id

            await update.message.reply_text(
                "أرسل اسم المشرف:"
            )
            return ADDING_ADMIN

        except ValueError:
            await update.message.reply_text(
                "❌ معرف غير صحيح! يرجى إرسال رقم صحيح."
            )
            return ENTERING_ADMIN_USER_ID

    async def handle_admin_name_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle admin name entry"""
        admin_name = update.message.text.strip()

        if not admin_name:
            await update.message.reply_text("❌ لا يمكن ترك الاسم فارغاً!")
            return ADDING_ADMIN

        user_id = context.user_data.get('new_admin_user_id')

        message = f"📋 **تأكيد إضافة مشرف**\n\n"
        message += f"الاسم: {admin_name}\n"
        message += f"معرف المستخدم: {user_id}\n\n"
        message += "سيتم منحه صلاحيات المشرف في البوت.\n\n"
        message += "هل تريد المتابعة؟"

        keyboard = [
            [InlineKeyboardButton("✅ تأكيد الإضافة", callback_data=f"confirm_add_admin_{user_id}_{admin_name}")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_admin")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return CONFIRMING_ADMIN_ADD

    async def handle_admin_selection_for_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle admin selection for deletion"""
        text = update.message.text

        if text == "⬅️ العودة":
            return await self.show_admins_management(update, context)

        admins = data_manager.get_admins()
        selected_admin_id = None

        for admin_id, admin_data in admins.items():
            expected_text = f"{admin_data['name']} - {admin_data['user_id']}"
            if text == expected_text:
                # Check if trying to delete main admin
                if admin_data['user_id'] == ADMIN_ID:
                    await update.message.reply_text(
                        "❌ لا يمكن حذف المشرف الرئيسي!",
                        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("⬅️ العودة")]], resize_keyboard=True)
                    )
                    return SELECTING_ADMIN_TO_DELETE

                selected_admin_id = admin_id
                context.user_data['admin_to_delete'] = admin_id
                break

        if not selected_admin_id:
            await update.message.reply_text("يرجى اختيار مشرف من القائمة.")
            return SELECTING_ADMIN_TO_DELETE

        admin_data = admins[selected_admin_id]

        message = f"⚠️ **تأكيد حذف المشرف**\n\n"
        message += f"الاسم: {admin_data['name']}\n"
        message += f"المعرف: {admin_data['user_id']}\n\n"
        message += "سيتم سحب صلاحيات المشرف من البوت.\n\n"
        message += "هل أنت متأكد من حذف هذا المشرف؟"

        keyboard = [
            [InlineKeyboardButton("✅ حذف المشرف", callback_data=f"confirm_delete_admin_{selected_admin_id}")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_delete_admin")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return CONFIRMING_ADMIN_DELETE

    async def handle_admin_callbacks(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle admin management callbacks"""
        query = update.callback_query
        await query.answer()
        data = query.data

        if data.startswith("confirm_add_admin_"):
            parts = data.replace("confirm_add_admin_", "").split("_", 1)
            user_id = int(parts[0])
            admin_name = parts[1]

            try:
                await query.edit_message_text("⏳ جاري إضافة المشرف...")

                # Add admin to database
                data_manager.add_admin(user_id, admin_name)

                # Send notification to new admin
                try:
                    bot_name = data_manager.get_bot_name(english=False)
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"🎉 **تم منحك صلاحيات المشرف**\n\nتم تعيينك كمشرف في بوت {bot_name}\n\nيمكنك الآن الوصول إلى لوحة التحكم."
                    )
                except Exception as e:
                    logger.error(f"Failed to notify new admin: {e}")

                success_message = f"✅ تمت إضافة المشرف بنجاح!\n\n"
                success_message += f"📝 الاسم: {admin_name}\n"
                success_message += f"🆔 المعرف: {user_id}\n\n"
                success_message += "تم منحه صلاحيات الوصول للوحة التحكم."

                await query.edit_message_text(success_message, parse_mode='Markdown')
                logger.info(f"Admin added: {admin_name} ({user_id})")

            except Exception as e:
                logger.error(f"Error adding admin: {e}")
                await query.edit_message_text(f"❌ حدث خطأ في إضافة المشرف: {str(e)}")

            context.user_data.clear()
            return MANAGING_ADMINS

        elif data == "cancel_add_admin":
            await query.edit_message_text("❌ تم إلغاء إضافة المشرف.")
            context.user_data.clear()
            return MANAGING_ADMINS

        elif data.startswith("confirm_delete_admin_"):
            admin_id = data.replace("confirm_delete_admin_", "")

            try:
                admins = data_manager.get_admins()

                if admin_id in admins:
                    admin_data = admins[admin_id]
                    user_id = admin_data['user_id']

                    # Prevent deleting main admin
                    if user_id == ADMIN_ID:
                        await query.edit_message_text("❌ لا يمكن حذف المشرف الرئيسي!")
                        return MANAGING_ADMINS

                    await query.edit_message_text("⏳ جاري حذف المشرف...")

                    # Delete from database
                    success = data_manager.delete_admin(admin_id)

                    if success:
                        success_message = f"✅ تم حذف المشرف بنجاح!\n\n"
                        success_message += f"📝 الاسم: {admin_data['name']}\n"
                        success_message += f"🆔 المعرف: {user_id}\n\n"
                        success_message += "تم سحب صلاحياته من البوت."

                        await query.edit_message_text(success_message, parse_mode='Markdown')

                        # Send notification to removed admin
                        try:
                            bot_name = data_manager.get_bot_name(english=False)
                            await context.bot.send_message(
                                chat_id=user_id,
                                text=f"📢 **تم سحب صلاحيات المشرف**\n\nتم إلغاء تعيينك كمشرف في بوت {bot_name}"
                            )
                        except Exception as e:
                            logger.error(f"Failed to notify removed admin: {e}")
                    else:
                        await query.edit_message_text("❌ فشل في حذف المشرف.")
                else:
                    await query.edit_message_text("❌ المشرف غير موجود.")
            except Exception as e:
                logger.error(f"Error deleting admin: {e}")
                await query.edit_message_text(f"❌ حدث خطأ في حذف المشرف: {str(e)}")

            context.user_data.clear()
            return MANAGING_ADMINS

        elif data == "cancel_delete_admin":
            await query.edit_message_text("❌ تم إلغاء حذف المشرف.")
            context.user_data.clear()
            return MANAGING_ADMINS

        return MANAGING_ADMINS

    async def show_pending_orders(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show pending orders"""
        pending_orders = data_manager.get_pending_orders()

        if not pending_orders:
            await update.message.reply_text("لا توجد طلبات معلقة.")
            return ADMIN_PANEL

        message = "📋 **الطلبات المعلقة:**\n\n"

        for order_id, order in pending_orders.items():
            # Get item details
            if order['service_type'] == 'app':
                items = data_manager.get_apps()
            else:
                items = data_manager.get_games()

            item_data = items.get(order['item_id'], {})
            category_data = item_data.get('categories', {}).get(order['category_id'], {})

            message += f"🆔 {order_id}\n"
            message += f"👤 {order['username']}\n"
            message += f"🎮 {item_data.get('name', 'N/A')}\n"
            message += f"💰 {order['price']} SYP\n"
            message += "─────────────\n"

        await update.message.reply_text(message, parse_mode='Markdown')
        return ADMIN_PANEL

    async def handle_add_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle adding balance to user"""
        try:
            parts = update.message.text.split()
            if len(parts) != 2:
                raise ValueError

            user_id = int(parts[0])
            amount = int(parts[1])

            if amount <= 0:
                raise ValueError

            data_manager.update_user_balance(user_id, amount)

            await update.message.reply_text(f"✅ تم إضافة {amount} SYP لرصيد المستخدم {user_id}")

            # Notify user
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"💰 تم شحن رصيدك بمبلغ {amount} SYP"
                )
            except Exception as e:
                logger.error(f"Failed to notify user about balance addition: {e}")

            return ADMIN_PANEL

        except ValueError:
            await update.message.reply_text("صيغة خاطئة. استخدم: user_id amount\nمثال: 123456789 5000")
            return ADD_BALANCE

    async def handle_support_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle support messages"""
        text = update.message.text

        if text == "إلغاء":
            await update.message.reply_text("تم إلغاء إرسال الرسالة.")
            return await self.start(update, context)

        user = update.effective_user

        # Send to admin
        support_message = f"💬 **رسالة دعم**\n\n"
        support_message += f"👤 من: @{user.username or user.first_name} ({user.id})\n"
        support_message += f"📝 الرسالة: {text}\n"
        support_message += f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=support_message,
                parse_mode='Markdown'
            )

            await update.message.reply_text("✅ تم إرسال رسالتك للدعم الفني. سيتم الرد عليك قريباً.")
        except Exception as e:
            logger.error(f"Failed to send support message: {e}")
            await update.message.reply_text("حدث خطأ في إرسال الرسالة. يرجى المحاولة لاحقاً.")

        return await self.start(update, context)

    async def show_apps_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show apps management interface"""
        message = "📱🎮 **إدارة التطبيقات والألعاب**\n\nاختر العملية:"

        keyboard = [
            [KeyboardButton("عرض التطبيقات المتاحة 📱")],
            [KeyboardButton("عرض الألعاب المتاحة 🎮")],
            [KeyboardButton("إضافة تطبيق/لعبة جديدة ➕")],
            [KeyboardButton("إدارة الفئات 🏷️")],
            [KeyboardButton("تعديل/حذف تطبيق 🗑️"), KeyboardButton("تعديل/حذف فئة ✏️")],
            [KeyboardButton("⬅️ العودة للوحة التحكم")]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return MANAGING_APPS

    async def handle_apps_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle apps management menu selection"""
        text = update.message.text

        if text == "عرض التطبيقات المتاحة 📱":
            apps = data_manager.get_apps()
            if not apps:
                await update.message.reply_text("لا توجد تطبيقات متاحة حالياً.")
            else:
                message = "📱 **التطبيقات المتاحة:**\n\n"
                for app_id, app_data in apps.items():
                    message += f"🔹 {app_data['name']} (ID: {app_id})\n"
                    for cat_id, cat_data in app_data['categories'].items():
                        if cat_data['type'] == 'fixed':
                            message += f"   • {cat_data['name']}: {cat_data['price']} SYP\n"
                        else:
                            message += f"   • {cat_data['name']}: {cat_data['price_per_unit']} SYP/وحدة\n"
                    message += "\n"
                await update.message.reply_text(message, parse_mode='Markdown')
            return MANAGING_APPS

        elif text == "عرض الألعاب المتاحة 🎮":
            games = data_manager.get_games()
            if not games:
                await update.message.reply_text("لا توجد ألعاب متاحة حالياً.")
            else:
                message = "🎮 **الألعاب المتاحة:**\n\n"
                for game_id, game_data in games.items():
                    message += f"🔹 {game_data['name']} (ID: {game_id})\n"
                    for cat_id, cat_data in game_data['categories'].items():
                        if cat_data['type'] == 'fixed':
                            message += f"   • {cat_data['name']}: {cat_data['price']} SYP\n"
                        else:
                            message += f"   • {cat_data['name']}: {cat_data['price_per_unit']} SYP/وحدة\n"
                    message += "\n"
                await update.message.reply_text(message, parse_mode='Markdown')
            return MANAGING_APPS

        elif text == "إضافة تطبيق/لعبة جديدة ➕":
            message = "اختر نوع الخدمة:"
            keyboard = [
                [KeyboardButton("تطبيق 📱")],
                [KeyboardButton("لعبة 🎮")],
                [KeyboardButton("⬅️ العودة")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(message, reply_markup=reply_markup)
            return SELECTING_APP_TYPE

        elif text == "إدارة الفئات 🏷️":
            return await self.show_categories_management(update, context)

        elif text == "تعديل/حذف تطبيق 🗑️":
            return await self.show_delete_action_selection(update, context, 'app')

        elif text == "تعديل/حذف فئة ✏️":
            return await self.show_delete_action_selection(update, context, 'category')

        elif text == "⬅️ العودة للوحة التحكم":
            return await self.show_admin_panel(update, context)

        else:
            await update.message.reply_text("يرجى اختيار خيار من القائمة.")
            return MANAGING_APPS

    async def handle_app_type_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle app type selection (app or game)"""
        text = update.message.text

        if text == "تطبيق 📱":
            context.user_data['adding_service_type'] = 'app'
            await update.message.reply_text("أدخل اسم التطبيق:")
            return ENTERING_APP_NAME

        elif text == "لعبة 🎮":
            context.user_data['adding_service_type'] = 'game'
            await update.message.reply_text("أدخل اسم اللعبة:")
            return ENTERING_APP_NAME

        elif text == "⬅️ العودة":
            return await self.show_apps_management(update, context)

        else:
            await update.message.reply_text("يرجى اختيار نوع الخدمة.")
            return SELECTING_APP_TYPE

    async def handle_app_name_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle app/game name entry"""
        app_name = update.message.text.strip()
        service_type = context.user_data.get('adding_service_type')

        if not app_name:
            await update.message.reply_text("يرجى إدخال اسم صحيح.")
            return ENTERING_APP_NAME

        # Generate app ID from name
        app_id = app_name.lower().replace(" ", "_").replace("-", "_")

        # Add to database
        data_manager.add_app_or_game(app_id, app_name, service_type)

        service_name = "التطبيق" if service_type == 'app' else "اللعبة"
        await update.message.reply_text(f"✅ تم إضافة {service_name} '{app_name}' بنجاح!")

        return await self.show_apps_management(update, context)

    async def show_categories_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show categories management interface"""
        message = "🏷️ **إدارة الفئات**\n\nاختر نوع الخدمة:"

        keyboard = [
            [KeyboardButton("فئة تطبيق 📱")],
            [KeyboardButton("فئة لعبة 🎮")],
            [KeyboardButton("⬅️ العودة")]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return SELECTING_CATEGORY_SERVICE

    async def handle_category_service_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle category service type selection"""
        text = update.message.text

        if text == "فئة تطبيق 📱":
            context.user_data['category_service_type'] = 'app'
            apps = data_manager.get_apps()

            if not apps:
                await update.message.reply_text("لا توجد تطبيقات متاحة. يرجى إضافة تطبيق أولاً.")
                return await self.show_categories_management(update, context)

            message = "اختر التطبيق:"
            keyboard = []
            for app_id, app_data in apps.items():
                keyboard.append([KeyboardButton(app_data['name'])])
            keyboard.append([KeyboardButton("⬅️ العودة")])

            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(message, reply_markup=reply_markup)
            return SELECTING_CATEGORY_APP

        elif text == "فئة لعبة 🎮":
            context.user_data['category_service_type'] = 'game'
            games = data_manager.get_games()

            if not games:
                await update.message.reply_text("لا توجد ألعاب متاحة. يرجى إضافة لعبة أولاً.")
                return await self.show_categories_management(update, context)

            message = "اختر اللعبة:"
            keyboard = []
            for game_id, game_data in games.items():
                keyboard.append([KeyboardButton(game_data['name'])])
            keyboard.append([KeyboardButton("⬅️ العودة")])

            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(message, reply_markup=reply_markup)
            return SELECTING_CATEGORY_APP

        elif text == "⬅️ العودة":
            return await self.show_apps_management(update, context)

        else:
            await update.message.reply_text("يرجى اختيار نوع الخدمة.")
            return SELECTING_CATEGORY_SERVICE

    async def handle_category_app_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle category app/game/payment selection"""
        text = update.message.text
        service_type = context.user_data.get('category_service_type')

        if text == "⬅️ العودة":
            # Check if this is for payments or apps/games
            if service_type in ['app', 'game']:
                return await self.show_categories_management(update, context)
            else:
                return await self.show_payments_management(update, context)

        # Find the selected item
        if service_type == 'app':
            items = data_manager.get_apps()
        elif service_type == 'game':
            items = data_manager.get_games()
        else:
            # This is for payments
            items = data_manager.get_payments()

        selected_item = None
        for item_id, item_data in items.items():
            if item_data['name'] == text:
                selected_item = item_id
                break

        if not selected_item:
            await update.message.reply_text("يرجى اختيار من القائمة المتاحة.")
            return SELECTING_CATEGORY_APP

        context.user_data['selected_app_for_category'] = selected_item

        message = "اختر نوع الفئة:"
        keyboard = [
            [KeyboardButton("فئة ثابتة 💰")],
            [KeyboardButton("فئة حسب الكمية 📊")],
            [KeyboardButton("⬅️ العودة")]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup)
        return SELECTING_CATEGORY_TYPE

    async def handle_category_type_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle category type selection"""
        text = update.message.text
        service_type = context.user_data.get('category_service_type')

        if text == "فئة ثابتة 💰":
            context.user_data['category_pricing_type'] = 'fixed'
            # For all services (apps, games, payments), go to bulk fixed categories entry
            await update.message.reply_text(
                "أدخل الفئات الثابتة بالصيغة التالية:\n"
                "اسم الفئة=السعر\n\n"
                "مثال:\n"
                "60 UC=2000\n"
                "300 UC=8000\n"
                "500 UC=12000\n\n"
                "يمكنك إضافة عدة فئات في رسالة واحدة، كل فئة في سطر منفصل."
            )
            return ENTERING_FIXED_CATEGORIES

        elif text == "فئة حسب الكمية 📊":
            context.user_data['category_pricing_type'] = 'quantity'
            await update.message.reply_text("أدخل اسم الفئة:")
            return ENTERING_QUANTITY_CATEGORY_NAME

        elif text == "⬅️ العودة":
            return await self.handle_category_app_selection(update, context)

        else:
            await update.message.reply_text("يرجى اختيار نوع الفئة.")
            return SELECTING_CATEGORY_TYPE

    async def handle_fixed_categories_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle fixed categories entry"""
        text = update.message.text.strip()
        service_type = context.user_data.get('category_service_type')
        app_id = context.user_data.get('selected_app_for_category')

        if not text:
            await update.message.reply_text("يرجى إدخال الفئات بالصيغة الصحيحة.")
            return ENTERING_FIXED_CATEGORIES

        lines = text.split('\n')
        added_categories = []
        failed_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if '=' not in line:
                failed_lines.append(f"• {line} (صيغة خاطئة)")
                continue

            try:
                name, price = line.split('=', 1)
                name = name.strip()
                price_str = price.strip()

                if not name:
                    failed_lines.append(f"• {line} (اسم الفئة فارغ)")
                    continue

                price = int(price_str)

                if price <= 0:
                    failed_lines.append(f"• {line} (السعر يجب أن يكون موجب)")
                    continue

                category_id = name.lower().replace(" ", "_").replace("=", "").replace("-", "_")

                # Create appropriate category data based on service type
                if service_type in ['app', 'game']:
                    # For apps and games, only basic category data is needed
                    category_data = {
                        "name": name,
                        "price": price,
                        "type": "fixed"
                    }
                    data_manager.add_category(service_type, app_id, category_id, category_data)
                else:
                    # For payment services, include payment-specific fields
                    category_data = {
                        "name": name,
                        "price": price,
                        "type": "fixed",
                        "input_type": "none",
                        "input_label": "",
                        "pricing_type": "fixed"
                    }
                    data_manager.add_payment_category(app_id, category_id, category_data)

                added_categories.append(f"• {name}: {price:,} SYP")

            except ValueError:
                failed_lines.append(f"• {line} (السعر يجب أن يكون رقم)")
                continue

        # Show results
        message = ""
        if added_categories:
            message += "✅ تم إضافة الفئات التالية:\n\n" + "\n".join(added_categories)

        if failed_lines:
            if message:
                message += "\n\n"
            message += "❌ فشل في إضافة:\n\n" + "\n".join(failed_lines)

        if not added_categories and not failed_lines:
            message = "❌ لم يتم إدخال أي فئات. تأكد من الصيغة الصحيحة:\nاسم الفئة=السعر"

        await update.message.reply_text(message)

        # Return to appropriate management screen
        if service_type in ['app', 'game']:
            return await self.show_categories_management(update, context)
        else:
            return await self.show_payments_management(update, context)

    async def handle_quantity_category_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle quantity category name entry"""
        category_name = update.message.text.strip()

        if not category_name:
            await update.message.reply_text("يرجى إدخال اسم صحيح للفئة:")
            return ENTERING_QUANTITY_CATEGORY_NAME

        context.user_data['quantity_category_name'] = category_name
        service_type = context.user_data.get('category_service_type')
        pricing_type = context.user_data.get('category_pricing_type', 'quantity')

        # For payment services with fixed pricing, go directly to price entry
        if service_type not in ['app', 'game'] and pricing_type == 'fixed':
            await update.message.reply_text("أدخل سعر هذه الفئة بـ SYP:")
            return ENTERING_CATEGORY_PRICE
        else:
            await update.message.reply_text("أدخل أقل طلب:")
            return ENTERING_MIN_ORDER

    async def handle_min_order_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle minimum order entry"""
        try:
            min_order = int(update.message.text.strip())
            context.user_data['min_order'] = min_order

            await update.message.reply_text("أدخل أقصى طلب:")
            return ENTERING_MAX_ORDER

        except ValueError:
            await update.message.reply_text("يرجى إدخال رقم صحيح لأقل طلب:")
            return ENTERING_MIN_ORDER

    async def handle_max_order_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle maximum order entry"""
        try:
            max_order = int(update.message.text.strip())
            min_order = context.user_data.get('min_order', 1)

            if max_order <= min_order:
                await update.message.reply_text(f"أقصى طلب يجب أن يكون أكبر من أقل طلب ({min_order}). يرجى إدخال رقم أكبر:")
                return ENTERING_MAX_ORDER

            context.user_data['max_order'] = max_order

            await update.message.reply_text("أدخل السعر لكل وحدة واحدة:")
            return ENTERING_PRICE_PER_UNIT

        except ValueError:
            await update.message.reply_text("يرجى إدخال رقم صحيح لأقصى طلب:")
            return ENTERING_MAX_ORDER

    async def handle_price_per_unit_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle price per unit entry"""
        try:
            price_per_unit = float(update.message.text.strip())

            service_type = context.user_data.get('category_service_type')
            app_id = context.user_data.get('selected_app_for_category')
            category_name = context.user_data.get('quantity_category_name')
            min_order = context.user_data.get('min_order')
            max_order = context.user_data.get('max_order')

            category_id = category_name.lower().replace(" ", "_")

            if service_type in ['app', 'game']:
                # For apps and games, add category directly without asking for input type
                category_data = {
                    "name": category_name,
                    "price_per_unit": price_per_unit,
                    "min_order": min_order,
                    "max_order": max_order,
                    "type": "quantity"
                }
                data_manager.add_category(service_type, app_id, category_id, category_data)

                message = f"✅ تم إضافة فئة '{category_name}' بنجاح!\n\n"
                message += f"• السعر لكل وحدة: {price_per_unit:,} SYP\n"
                message += f"• أقل طلب: {min_order}\n"
                message += f"• أقصى طلب: {max_order}"

                await update.message.reply_text(message)
                return await self.show_categories_management(update, context)

            else:
                # For payment services, add directly without asking for input type
                category_data = {
                    "name": category_name,
                    "price_per_unit": price_per_unit,
                    "min_order": min_order,
                    "max_order": max_order,
                    "type": "quantity",
                    "input_type": "none",
                    "input_label": "",
                    "pricing_type": "quantity"
                }

                # Add category to service
                success = data_manager.add_payment_category(app_id, category_id, category_data)

                if success:
                    message = f"✅ تم إضافة فئة '{category_name}' بنجاح!\n\n"
                    message += f"💰 السعر لكل وحدة: {price_per_unit:,} SYP\n"
                    message += f"📊 أقل طلب: {min_order}\n"
                    if max_order:
                        message += f"📊 أقصى طلب: {max_order}\n"

                    await update.message.reply_text(message)

                    # Clear category-specific data
                    for key in ['quantity_category_name', 'category_price', 'category_price_per_unit', 'min_order', 'max_order', 'category_pricing_type']:
                        context.user_data.pop(key, None)

                    return await self.show_payments_management(update, context)
                else:
                    await update.message.reply_text("❌ حدث خطأ في إضافة الفئة.")
                    return await self.show_payments_management(update, context)

        except ValueError:
            await update.message.reply_text("يرجى إدخال رقم صحيح للسعر:")
            return ENTERING_PRICE_PER_UNIT

    async def show_delete_action_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, item_type: str) -> int:
        """Show delete action selection"""
        context.user_data['delete_item_type'] = item_type

        if item_type == 'app':
            message = "🗑️ **حذف/تعديل التطبيقات والألعاب**\n\nاختر العملية:"
        else:
            message = "✏️ **حذف/تعديل الفئات**\n\nاختر العملية:"

        keyboard = [
            [KeyboardButton("حذف 🗑️")],
            [KeyboardButton("تعديل ✏️")],
            [KeyboardButton("⬅️ العودة")]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return SELECTING_DELETE_ACTION

    async def handle_delete_action_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle delete action selection"""
        text = update.message.text
        item_type = context.user_data.get('delete_item_type')

        if text == "حذف 🗑️":
            context.user_data['delete_action'] = 'delete'
            if item_type == 'app':
                return await self.show_delete_service_type_selection(update, context)
            else:  # category
                return await self.show_delete_category_service_selection(update, context)

        elif text == "تعديل ✏️":
            await update.message.reply_text("خاصية التعديل ستكون متاحة قريباً...")
            return await self.show_apps_management(update, context)

        elif text == "⬅️ العودة":
            return await self.show_apps_management(update, context)

        else:
            await update.message.reply_text("يرجى اختيار عملية صحيحة.")
            return SELECTING_DELETE_ACTION

    async def show_delete_service_type_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show service type selection for deletion"""
        message = "اختر نوع الخدمة للحذف:"

        keyboard = [
            [KeyboardButton("حذف تطبيق 📱")],
            [KeyboardButton("حذف لعبة 🎮")],
            [KeyboardButton("⬅️ العودة")]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup)

        return SELECTING_DELETE_SERVICE_TYPE

    async def handle_delete_service_type_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle delete service type selection"""
        text = update.message.text

        if text == "حذف تطبيق 📱":
            context.user_data['delete_service_type'] = 'app'
            apps = data_manager.get_apps()

            if not apps:
                await update.message.reply_text("لا توجد تطبيقات متاحة للحذف.")
                return await self.show_apps_management(update, context)

            message = "اختر التطبيق المراد حذفه:"
            keyboard = []
            for app_id, app_data in apps.items():
                keyboard.append([KeyboardButton(app_data['name'])])
            keyboard.append([KeyboardButton("⬅️ العودة")])

            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(message, reply_markup=reply_markup)
            return SELECTING_DELETE_ITEM

        elif text == "حذف لعبة 🎮":
            context.user_data['delete_service_type'] = 'game'
            games = data_manager.get_games()

            if not games:
                await update.message.reply_text("لا توجد ألعاب متاحة للحذف.")
                return await self.show_apps_management(update, context)

            message = "اختر اللعبة المراد حذفها:"
            keyboard = []
            for game_id, game_data in games.items():
                keyboard.append([KeyboardButton(game_data['name'])])
            keyboard.append([KeyboardButton("⬅️ العودة")])

            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(message, reply_markup=reply_markup)
            return SELECTING_DELETE_ITEM

        elif text == "⬅️ العودة":
            return await self.show_delete_action_selection(update, context, context.user_data.get('delete_item_type'))

        else:
            await update.message.reply_text("يرجى اختيار نوع الخدمة.")
            return SELECTING_DELETE_SERVICE_TYPE

    async def handle_delete_item_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle delete item selection"""
        text = update.message.text
        service_type = context.user_data.get('delete_service_type')

        if text == "⬅️ العودة":
            return await self.show_delete_service_type_selection(update, context)

        # Find the selected item
        if service_type == 'app':
            items = data_manager.get_apps()
        else:
            items = data_manager.get_games()

        selected_item_id = None
        selected_item_name = None
        for item_id, item_data in items.items():
            if item_data['name'] == text:
                selected_item_id = item_id
                selected_item_name = item_data['name']
                break

        if not selected_item_id:
            await update.message.reply_text("يرجى اختيار من القائمة المتاحة.")
            return SELECTING_DELETE_ITEM

        context.user_data['delete_item_id'] = selected_item_id
        context.user_data['delete_item_name'] = selected_item_name

        # Show confirmation message
        service_name = "التطبيق" if service_type == 'app' else "اللعبة"
        categories_count = len(items[selected_item_id]['categories'])

        message = f"⚠️ **تأكيد الحذف**\n\n"
        message += f"هل أنت متأكد من حذف {service_name}: **{selected_item_name}**؟\n\n"
        message += f"📦 عدد الفئات: {categories_count}\n"
        message += f"🗑️ سيتم حذف {service_name} **بالكامل** مع جميع فئاته!\n\n"
        message += "⚠️ **هذا الإجراء لا يمكن التراجع عنه!**"

        keyboard = [
            [KeyboardButton("✅ تأكيد الحذف")],
            [KeyboardButton("❌ إلغاء")]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return CONFIRMING_DELETE

    async def handle_delete_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle delete confirmation"""
        text = update.message.text

        if text == "✅ تأكيد الحذف":
            service_type = context.user_data.get('delete_service_type')
            item_id = context.user_data.get('delete_item_id')
            item_name = context.user_data.get('delete_item_name')

            # Perform deletion
            success = data_manager.delete_app_or_game(service_type, item_id)

            if success:
                service_name = "التطبيق" if service_type == 'app' else "اللعبة"
                await update.message.reply_text(f"✅ تم حذف {service_name} '{item_name}' بنجاح مع جميع فئاته!")
            else:
                await update.message.reply_text("❌ حدث خطأ في عملية الحذف.")

            return await self.show_apps_management(update, context)

        elif text == "❌ إلغاء":
            await update.message.reply_text("تم إلغاء عملية الحذف.")
            return await self.show_apps_management(update, context)

        else:
            await update.message.reply_text("يرجى اختيار تأكيد الحذف أو الإلغاء.")
            return CONFIRMING_DELETE

    async def show_delete_category_service_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show category service selection for deletion"""
        message = "اختر نوع الخدمة للحذف من فئاتها:"

        keyboard = [
            [KeyboardButton("فئات التطبيقات 📱")],
            [KeyboardButton("فئات الألعاب 🎮")],
            [KeyboardButton("⬅️ العودة")]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup)

        return SELECTING_DELETE_CATEGORY_SERVICE

    async def handle_delete_category_service_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle delete category service selection"""
        text = update.message.text

        if text == "فئات التطبيقات 📱":
            context.user_data['delete_category_service_type'] = 'app'
            apps = data_manager.get_apps()

            if not apps:
                await update.message.reply_text("لا توجد تطبيقات متاحة.")
                return await self.show_apps_management(update, context)

            message = "اختر التطبيق:"
            keyboard = []
            for app_id, app_data in apps.items():
                if app_data['categories']:  # Only show apps with categories
                    keyboard.append([KeyboardButton(app_data['name'])])

            if not keyboard:
                await update.message.reply_text("لا توجد تطبيقات تحتوي على فئات.")
                return await self.show_apps_management(update, context)

            keyboard.append([KeyboardButton("⬅️ العودة")])
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(message, reply_markup=reply_markup)
            return SELECTING_DELETE_CATEGORY_APP

        elif text == "فئات الألعاب 🎮":
            context.user_data['delete_category_service_type'] = 'game'
            games = data_manager.get_games()

            if not games:
                await update.message.reply_text("لا توجد ألعاب متاحة.")
                return await self.show_apps_management(update, context)

            message = "اختر اللعبة:"
            keyboard = []
            for game_id, game_data in games.items():
                if game_data['categories']:  # Only show games with categories
                    keyboard.append([KeyboardButton(game_data['name'])])

            if not keyboard:
                await update.message.reply_text("لا توجد ألعاب تحتوي على فئات.")
                return await self.show_apps_management(update, context)

            keyboard.append([KeyboardButton("⬅️ العودة")])
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(message, reply_markup=reply_markup)
            return SELECTING_DELETE_CATEGORY_APP

        elif text == "⬅️ العودة":
            return await self.show_delete_action_selection(update, context, context.user_data.get('delete_item_type'))

        else:
            await update.message.reply_text("يرجى اختيار نوع الخدمة.")
            return SELECTING_DELETE_CATEGORY_SERVICE

    async def handle_delete_category_app_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle delete category app selection"""
        text = update.message.text
        service_type = context.user_data.get('delete_category_service_type')

        if text == "⬅️ العودة":
            return await self.show_delete_category_service_selection(update, context)

        # Find the selected app/game
        if service_type == 'app':
            items = data_manager.get_apps()
        else:
            items = data_manager.get_games()

        selected_item_id = None
        for item_id, item_data in items.items():
            if item_data['name'] == text:
                selected_item_id = item_id
                break

        if not selected_item_id:
            await update.message.reply_text("يرجى اختيار من القائمة المتاحة.")
            return SELECTING_DELETE_CATEGORY_APP

        context.user_data['delete_category_app_id'] = selected_item_id

        # Show categories for this app/game
        item_data = items[selected_item_id]
        categories = item_data['categories']

        if not categories:
            service_name = "التطبيق" if service_type == 'app' else "اللعبة"
            await update.message.reply_text(f"لا توجد فئات في {service_name} المحدد.")
            return await self.show_apps_management(update, context)

        message = "اختر الفئة المراد حذفها:"
        keyboard = []
        for cat_id, cat_data in categories.items():
            keyboard.append([KeyboardButton(cat_data['name'])])
        keyboard.append([KeyboardButton("⬅️ العودة")])

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup)

        return SELECTING_DELETE_CATEGORY

    async def handle_delete_category_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle delete category selection"""
        text = update.message.text
        service_type = context.user_data.get('delete_category_service_type')
        app_id = context.user_data.get('delete_category_app_id')

        if text == "⬅️ العودة":
            return await self.handle_delete_category_service_selection(update, context)

        # Find the selected category
        if service_type == 'app':
            items = data_manager.get_apps()
        else:
            items = data_manager.get_games()

        item_data = items[app_id]
        selected_category_id = None
        selected_category_name = None

        for cat_id, cat_data in item_data['categories'].items():
            if cat_data['name'] == text:
                selected_category_id = cat_id
                selected_category_name = cat_data['name']
                break

        if not selected_category_id:
            await update.message.reply_text("يرجى اختيار من القائمة المتاحة.")
            return SELECTING_DELETE_CATEGORY

        context.user_data['delete_category_id'] = selected_category_id
        context.user_data['delete_category_name'] = selected_category_name

        # Show confirmation message
        message = f"⚠️ **تأكيد حذف الفئة**\n\n"
        message += f"هل أنت متأكد من حذف الفئة: **{selected_category_name}**؟\n"
        message += f"من {item_data['name']}\n\n"
        message += "⚠️ **هذا الإجراء لا يمكن التراجع عنه!**"

        keyboard = [
            [KeyboardButton("✅ تأكيد حذف الفئة")],
            [KeyboardButton("❌ إلغاء")]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return CONFIRMING_DELETE_CATEGORY

    async def handle_delete_category_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle delete category confirmation"""
        text = update.message.text

        if text == "✅ تأكيد حذف الفئة":
            service_type = context.user_data.get('delete_category_service_type')
            app_id = context.user_data.get('delete_category_app_id')
            category_id = context.user_data.get('delete_category_id')
            category_name = context.user_data.get('delete_category_name')

            # Perform deletion
            success = data_manager.delete_category(service_type, app_id, category_id)

            if success:
                await update.message.reply_text(f"✅ تم حذف الفئة '{category_name}' بنجاح!")
            else:
                await update.message.reply_text("❌ حدث خطأ في عملية الحذف.")

            return await self.show_apps_management(update, context)

        elif text == "❌ إلغاء":
            await update.message.reply_text("تم إلغاء عملية الحذف.")
            return await self.show_apps_management(update, context)

        else:
            await update.message.reply_text("يرجى اختيار تأكيد الحذف أو الإلغاء.")
            return CONFIRMING_DELETE

    async def handle_support_username_setting(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle support username setting"""
        username = update.message.text.strip().replace("@", "")

        if not username:
            await update.message.reply_text("يرجى إدخال اسم مستخدم صحيح:")
            return SETTING_SUPPORT_USERNAME

        # Validate username format (basic validation)
        if not username.replace("_", "").isalnum() or len(username) < 3:
            await update.message.reply_text("اسم المستخدم غير صحيح. يجب أن يحتوي على أحرف وأرقام فقط وأن يكون أطول من 3 أحرف:")
            return SETTING_SUPPORT_USERNAME

        data_manager.set_support_username(username)

        await update.message.reply_text(f"✅ تم تعيين حساب الدعم: @{username}")

        return await self.show_admin_panel(update, context)

    async def show_payment_addresses_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show payment addresses management"""
        syriatel_address = data_manager.get_syriatel_address()
        shamcash_data = data_manager.get_shamcash_data()
        payeer_data = data_manager.get_payeer_data()
        usdt_data = data_manager.get_usdt_data()

        message = f"🏦 **إدارة عناوين الدفع**\n\n"
        message += f"📱 سيريتل كاش: `{syriatel_address}`\n"
        message += f"💰 شام كاش: `{shamcash_data['address']}` ({shamcash_data['exchange_rate']:,} SYP/USD)\n"
        message += f"💳 Payeer: `{payeer_data['address']}` ({payeer_data['exchange_rate']:,} SYP/USD)\n"
        message += f"🪙 USDT BEP-20: `{usdt_data['address']}` ({usdt_data['exchange_rate']:,} SYP/USDT)\n\n"
        message += "اختر العنوان المراد تعديله:"

        keyboard = [
            [KeyboardButton("تعيين عنوان سيريتل كاش 📱")],
            [KeyboardButton("تعيين بيانات شام كاش 💰")],
            [KeyboardButton("تعيين بيانات Payeer 💳")],
            [KeyboardButton("تعيين بيانات USDT BEP-20 🪙")],
            [KeyboardButton("⬅️ العودة للوحة التحكم")]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return MANAGING_PAYMENT_ADDRESSES

    async def handle_payment_addresses_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle payment addresses management selection"""
        text = update.message.text

        if text == "تعيين عنوان سيريتل كاش 📱":
            current_address = data_manager.get_syriatel_address()
            message = f"العنوان الحالي: `{current_address}`\n\n"
            message += "أدخل العنوان الجديد لسيريتل كاش:"
            await update.message.reply_text(message, parse_mode='Markdown')
            return SETTING_SYRIATEL_ADDRESS

        elif text == "تعيين بيانات شام كاش 💰":
            shamcash_data = data_manager.get_shamcash_data()
            message = f"💰 **إعدادات شام كاش الحالية:**\n\n"
            message += f"العنوان: `{shamcash_data['address']}`\n"
            message += f"سعر الصرف: {shamcash_data['exchange_rate']:,} SYP/USD\n\n"
            message += "أدخل العنوان الجديد وسعر الصرف بالصيغة التالية:\n"
            message += "`العنوان سعر_الصرف`\n\n"
            message += "مثال: `+963123456789 3000`"
            await update.message.reply_text(message, parse_mode='Markdown')
            return SETTING_SHAMCASH_ADDRESS

        elif text == "تعيين بيانات Payeer 💳":
            payeer_data = data_manager.get_payeer_data()
            message = f"💳 **إعدادات Payeer الحالية:**\n\n"
            message += f"العنوان: `{payeer_data['address']}`\n"
            message += f"سعر الصرف: {payeer_data['exchange_rate']:,} SYP/USD\n\n"
            message += "أدخل العنوان الجديد وسعر الصرف بالصيغة التالية:\n"
            message += "`العنوان سعر_الصرف`\n\n"
            message += "مثال: `P1234567890 3000`"
            await update.message.reply_text(message, parse_mode='Markdown')
            return SETTING_PAYEER_DATA

        elif text == "تعيين بيانات USDT BEP-20 🪙":
            usdt_data = data_manager.get_usdt_data()
            message = f"🪙 **إعدادات USDT BEP-20 الحالية:**\n\n"
            message += f"العنوان: `{usdt_data['address']}`\n"
            message += f"سعر الصرف: {usdt_data['exchange_rate']:,} SYP/USDT\n\n"
            message += "أدخل العنوان الجديد وسعر الصرف بالصيغة التالية:\n"
            message += "`العنوان سعر_الصرف`\n\n"
            message += "مثال: `0x1234567890abcdef1234567890abcdef12345678 3000`"
            await update.message.reply_text(message, parse_mode='Markdown')
            return SETTING_USDT_DATA

        elif text == "⬅️ العودة للوحة التحكم":
            return await self.show_admin_panel(update, context)

        else:
            await update.message.reply_text("يرجى اختيار خيار صحيح من القائمة.")
            return MANAGING_PAYMENT_ADDRESSES

    async def handle_syriatel_address_setting(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle Syriatel address setting"""
        address = update.message.text.strip()

        if not address:
            await update.message.reply_text("يرجى إدخال عنوان صحيح:")
            return SETTING_SYRIATEL_ADDRESS

        data_manager.set_syriatel_address(address)
        await update.message.reply_text(f"✅ تم تعيين عنوان سيريتل كاش: `{address}`", parse_mode='Markdown')

        return await self.show_payment_addresses_management(update, context)

    async def handle_shamcash_address_setting(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle Sham cash data setting"""
        try:
            parts = update.message.text.strip().split()
            if len(parts) != 2:
                raise ValueError

            address = parts[0]
            exchange_rate = int(parts[1])

            if exchange_rate <= 0:
                raise ValueError

            data_manager.set_shamcash_data(address, exchange_rate)
            await update.message.reply_text(
                f"✅ تم تعيين بيانات شام كاش:\n"
                f"العنوان: `{address}`\n"
                f"سعر الصرف: {exchange_rate:,} SYP/USD",
                parse_mode='Markdown'
            )

            return await self.show_payment_addresses_management(update, context)

        except ValueError:
            await update.message.reply_text(
                "❌ خطأ في الإدخال. يرجى إدخال البيانات بالصيغة الصحيحة:\n"
                "`العنوان سعر_الصرف`\n\n"
                "مثال: `+963123456789 3000`",
                parse_mode='Markdown'
            )
            return SETTING_SHAMCASH_ADDRESS

    async def handle_payeer_data_setting(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle Payeer data setting"""
        try:
            parts = update.message.text.strip().split()
            if len(parts) != 2:
                raise ValueError

            address = parts[0]
            exchange_rate = int(parts[1])

            if exchange_rate <= 0:
                raise ValueError

            data_manager.set_payeer_data(address, exchange_rate)
            await update.message.reply_text(
                f"✅ تم تعيين بيانات Payeer:\n"
                f"العنوان: `{address}`\n"
                f"سعر الصرف: {exchange_rate:,} SYP/USD",
                parse_mode='Markdown'
            )

            return await self.show_payment_addresses_management(update, context)

        except ValueError:
            await update.message.reply_text(
                "صيغة خاطئة. استخدم: `العنوان سعر_الصرف`\n"
                "مثال: `P1234567890 3000`",
                parse_mode='Markdown'
            )
            return SETTING_PAYEER_DATA

    async def handle_usdt_data_setting(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle USDT BEP-20 data setting"""
        try:
            parts = update.message.text.strip().split()
            if len(parts) != 2:
                raise ValueError

            address = parts[0]
            exchange_rate = int(parts[1])

            if exchange_rate <= 0:
                raise ValueError

            data_manager.set_usdt_data(address, exchange_rate)
            await update.message.reply_text(
                f"✅ تم تعيين بيانات USDT BEP-20:\n"
                f"العنوان: `{address}`\n"
                f"سعر الصرف: {exchange_rate:,} SYP/USDT",
                parse_mode='Markdown'
            )

            return await self.show_payment_addresses_management(update, context)

        except ValueError:
            await update.message.reply_text(
                "صيغة خاطئة. استخدم: `العنوان سعر_الصرف`\n"
                "مثال: `0x1234567890abcdef1234567890abcdef12345678 3000`",
                parse_mode='Markdown'
            )
            return SETTING_USDT_DATA

    async def show_charge_codes_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show charge codes management"""
        codes = data_manager.get_all_charge_codes()

        message = f"🏷️ **إدارة أكواد الشحن**\n\n"

        if codes:
            # Calculate statistics
            active_codes = [(code, data) for code, data in codes.items() if not data["used"]]
            used_codes = [(code, data) for code, data in codes.items() if data["used"]]

            # Calculate total values
            active_total = sum(code_data['value'] for _, code_data in active_codes)
            used_total = sum(code_data['value'] for _, code_data in used_codes)
            grand_total = active_total + used_total

            message += f"📊 **الإحصائيات:**\n"
            message += f"🟢 الأكواد النشطة: {len(active_codes)} ({active_total:,} SYP)\n"
            message += f"🔴 الأكواد المستخدمة: {len(used_codes)} ({used_total:,} SYP)\n"
            message += f"📈 المجموع: {len(codes)} ({grand_total:,} SYP)\n\n"

            # Show active codes
            if active_codes:
                message += "🟢 **الأكواد النشطة:**\n"
                for code, code_data in active_codes:
                    created_date = datetime.fromisoformat(code_data['created_at']).strftime('%m-%d %H:%M')
                    message += f"• `{code}` - {code_data['value']:,} SYP ({created_date})\n"
                message += "\n"

            # Show last 10 used codes
            if used_codes:
                message += "🔴 **آخر 10 أكواد مستخدمة:**\n"
                # Sort by used_at date (most recent first)
                sorted_used = sorted(used_codes, key=lambda x: x[1].get('used_at', ''), reverse=True)
                for code, code_data in sorted_used[:10]:
                    used_date = datetime.fromisoformat(code_data['used_at']).strftime('%m-%d %H:%M')
                    message += f"• `{code}` - {code_data['value']:,} SYP ({used_date})\n"

                if len(used_codes) > 10:
                    message += f"... و {len(used_codes) - 10} كود آخر\n"
        else:
            message += "لا توجد أكواد شحن مُولّدة بعد.\n\n"

        message += "\nاختر العملية:"

        keyboard = [
            [KeyboardButton("توليد كود شحن جديد ➕")],
            [KeyboardButton("عرض تفاصيل أكثر 📊")],
            [KeyboardButton("⬅️ العودة للوحة التحكم")]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return MANAGING_CHARGE_CODES

    async def handle_charge_codes_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle charge codes management selection"""
        text = update.message.text

        if text == "توليد كود شحن جديد ➕":
            await update.message.reply_text("أدخل قيمة كود الشحن بـ SYP:\n\nمثال: 5000")
            return ENTERING_CHARGE_CODE_VALUE

        elif text == "عرض تفاصيل أكثر 📊":
            codes = data_manager.get_all_charge_codes()

            if not codes:
                await update.message.reply_text("لا توجد أكواد شحن مُولّدة بعد.")
                return MANAGING_CHARGE_CODES

            # Separate active and used codes
            active_codes = [(code, data) for code, data in codes.items() if not data["used"]]
            used_codes = [(code, data) for code, data in codes.items() if data["used"]]

            # Calculate totals
            active_total = sum(code_data['value'] for _, code_data in active_codes)
            used_total = sum(code_data['value'] for _, code_data in used_codes)

            message = "📊 **تفاصيل أكواد الشحن:**\n\n"

            # Detailed statistics
            message += f"📈 **الإحصائيات التفصيلية:**\n"
            message += f"🟢 الأكواد النشطة: {len(active_codes)} كود\n"
            message += f"💰 القيمة الإجمالية للأكواد النشطة: {active_total:,} SYP\n\n"
            message += f"🔴 الأكواد المستخدمة: {len(used_codes)} كود\n"
            message += f"💰 القيمة الإجمالية للأكواد المستخدمة: {used_total:,} SYP\n\n"
            message += f"📊 المجموع الكلي: {len(codes)} كود\n"
            message += f"💎 القيمة الإجمالية: {active_total + used_total:,} SYP\n\n"

            # Show all active codes if any
            if active_codes:
                message += f"🟢 **جميع الأكواد النشطة ({len(active_codes)}):**\n"
                for code, code_data in active_codes:
                    created_date = datetime.fromisoformat(code_data['created_at']).strftime('%Y-%m-%d %H:%M')
                    message += f"• `{code}` - {code_data['value']:,} SYP\n  📅 تم إنشاؤه: {created_date}\n"
                message += "\n"

            # Show last 10 used codes with more details
            if used_codes:
                sorted_used = sorted(used_codes, key=lambda x: x[1].get('used_at', ''), reverse=True)
                message += f"🔴 **آخر 10 أكواد مستخدمة:**\n"
                for code, code_data in sorted_used[:10]:
                    created_date = datetime.fromisoformat(code_data['created_at']).strftime('%m-%d %H:%M')
                    used_date = datetime.fromisoformat(code_data['used_at']).strftime('%m-%d %H:%M')
                    message += f"• `{code}` - {code_data['value']:,} SYP\n"
                    message += f"  📅 أُنشئ: {created_date} | استُخدم: {used_date}\n"

                if len(used_codes) > 10:
                    remaining_value = sum(code_data['value'] for _, code_data in sorted_used[10:])
                    message += f"\n📋 الأكواد المتبقية: {len(used_codes) - 10} كود ({remaining_value:,} SYP)\n"

            await update.message.reply_text(message, parse_mode='Markdown')
            return MANAGING_CHARGE_CODES

        elif text == "⬅️ العودة للوحة التحكم":
            return await self.show_admin_panel(update, context)

        else:
            await update.message.reply_text("يرجى اختيار خيار صحيح من القائمة.")
            return MANAGING_CHARGE_CODES

    async def handle_charge_code_value_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle charge code value entry"""
        try:
            value = int(update.message.text.strip())
            if value <= 0:
                raise ValueError

            # Generate unique charge code
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

            context.user_data['charge_code'] = code
            context.user_data['charge_code_value'] = value

            message = f"🏷️ **تأكيد توليد كود الشحن**\n\n"
            message += f"الكود: `{code}`\n"
            message += f"القيمة: {value:,} SYP\n\n"
            message += "هل تريد إنشاء هذا الكود؟"

            keyboard = [
                [InlineKeyboardButton("✅ إنشاء الكود", callback_data="confirm_charge_code_creation")],
                [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_charge_code_creation")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

            return CONFIRMING_CHARGE_CODE_GENERATION

        except ValueError:
            await update.message.reply_text("يرجى إدخال قيمة صحيحة (رقم موجب):")
            return ENTERING_CHARGE_CODE_VALUE

    async def handle_charge_code_generation_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle charge code generation confirmation"""
        query = update.callback_query
        await query.answer()

        if query.data == "cancel_charge_code_creation":
            await query.edit_message_text("تم إلغاء إنشاء كود الشحن.")
            context.user_data.clear()
            return await self.show_charge_codes_management(update, context)

        elif query.data == "confirm_charge_code_creation":
            code = context.user_data.get('charge_code')
            value = context.user_data.get('charge_code_value')

            # Save the charge code
            data_manager.save_charge_code(code, value)

            message = f"✅ **تم إنشاء كود الشحن بنجاح!**\n\n"
            message += f"🏷️ الكود: `{code}`\n"
            message += f"💰 القيمة: {value:,} SYP\n"
            message += f"📅 تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            message += "يمكن للمستخدمين الآن استخدام هذا الكود لشحن رصيدهم."

            await query.edit_message_text(message, parse_mode='Markdown')

            context.user_data.clear()
            return MANAGING_CHARGE_CODES

    async def handle_payment_method_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle payment method selection"""
        text = update.message.text
        user_id = update.effective_user.id

        # Check subscription before processing
        is_subscribed = await self.check_channel_subscription(user_id, context)
        if not is_subscribed:
            return await self.start(update, context)

        if text == "كود شحن 🏷️":
            message = "🏷️ **شحن عبر كود الشحن**\n\n"
            message += "يرجى إدخال كود الشحن الخاص بك:\n\n"
            message += "💡 تأكد من كتابة الكود بشكل صحيح"

            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardRemove()
            )
            return ENTERING_CHARGE_CODE

        elif text == "سيريتل كاش 📱":
            syriatel_address = data_manager.get_syriatel_address()

            if syriatel_address == "0000":
                await update.message.reply_text(
                    "❌ الشحن عبر سيريتل كاش غير متاح حالياً\n\nيرجى اختيار طريقة دفع أخرى.",
                    reply_markup=ReplyKeyboardRemove()
                )
                return await self.start(update, context)

            message = f"📱 **شحن عبر سيريتل كاش**\n\n"
            message += f"📋 **خطوات الشحن:**\n"
            message += f"1️⃣ قم بتحويل المبلغ المراد شحنه عبر سيريتل كاش\n"
            message += f"2️⃣ استخدم طريقة **التحويل اليدوي** إلى العنوان التالي:\n\n"
            message += f"📮 العنوان: `{syriatel_address}`\n\n"
            message += f"3️⃣ بعد إتمام التحويل، أدخل رقم العملية:"

            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardRemove()
            )
            return ENTERING_SYRIATEL_TRANSACTION

        elif text == "شام كاش | Sham Cash":
            shamcash_data = data_manager.get_shamcash_data()

            if not shamcash_data or shamcash_data.get('address', '0000') == '0000':
                await update.message.reply_text(
                    "❌ الشحن عبر شام كاش غير متاح حالياً\n\nيرجى اختيار طريقة دفع أخرى.",
                    reply_markup=ReplyKeyboardRemove()
                )
                return await self.start(update, context)

            message = "💳 **شحن عبر شام كاش**\n\n"
            message += "اختر العملة المراد الدفع بها:"

            keyboard = [
                [KeyboardButton("ليرة سورية (SYP)")],
                [KeyboardButton("دولار أمريكي (USD)")],
                [KeyboardButton("⬅️ العودة للقائمة الرئيسية")]
            ]

            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            context.user_data['payment_method'] = 'shamcash'
            return SELECTING_SHAMCASH_CURRENCY

        elif text == "Payeer 💳":
            payeer_data = data_manager.get_payeer_data()

            if not payeer_data or payeer_data.get('address', '0000') == '0000':
                await update.message.reply_text(
                    "❌ الشحن عبر Payeer غير متاح حالياً\n\nيرجى اختيار طريقة دفع أخرى.",
                    reply_markup=ReplyKeyboardRemove()
                )
                return await self.start(update, context)

            exchange_rate = payeer_data.get('exchange_rate', 3000)
            address = payeer_data.get('address')

            message = f"💳 **شحن عبر Payeer**\n\n"
            message += f"💱 **سعر الصرف:** 1 USD = {exchange_rate:,} SYP\n\n"
            message += f"📋 **خطوات الشحن:**\n"
            message += f"1️⃣ قم بتحويل المبلغ المراد إيداعه عبر Payeer\n"
            message += f"2️⃣ استخدم عنوان الدفع التالي:\n\n"
            message += f"📮 `{address}`\n\n"
            message += f"3️⃣ بعد إتمام التحويل، أدخل رقم العملية:"

            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardRemove()
            )
            context.user_data['payment_method'] = 'payeer'
            return ENTERING_SYRIATEL_TRANSACTION

        elif text == "USDT BEP-20 🪙":
            usdt_data = data_manager.get_usdt_data()

            if not usdt_data or usdt_data.get('address', '0000') == '0000':
                await update.message.reply_text(
                    "❌ الشحن عبر USDT BEP-20 غير متاح حالياً\n\nيرجى اختيار طريقة دفع أخرى.",
                    reply_markup=ReplyKeyboardRemove()
                )
                return await self.start(update, context)

            exchange_rate = usdt_data.get('exchange_rate', 3000)
            address = usdt_data.get('address')

            message = f"🪙 **شحن عبر USDT BEP-20**\n\n"
            message += f"💱 **سعر الصرف:** 1 USDT = {exchange_rate:,} SYP\n\n"
            message += f"📋 **خطوات الشحن:**\n"
            message += f"1️⃣ قم بتحويل المبلغ المراد إيداعه عبر USDT (شبكة BEP-20)\n"
            message += f"2️⃣ استخدم عنوان المحفظة التالي:\n\n"
            message += f"📮 `{address}`\n\n"
            message += f"⚠️ **تنبيه:** تأكد من استخدام شبكة BEP-20 فقط\n\n"
            message += f"3️⃣ بعد إتمام التحويل، أدخل رقم العملية (Transaction Hash):"

            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardRemove()
            )
            context.user_data['payment_method'] = 'usdt_bep20'
            return ENTERING_SYRIATEL_TRANSACTION

        elif text == "⬅️ العودة للقائمة الرئيسية":
            return await self.start(update, context)

        else:
            await update.message.reply_text("يرجى اختيار طريقة دفع صحيحة.")
            return SELECTING_PAYMENT_METHOD

    async def handle_shamcash_currency_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle Sham Cash currency selection"""
        text = update.message.text
        user_id = update.effective_user.id

        # Check subscription before processing
        is_subscribed = await self.check_channel_subscription(user_id, context)
        if not is_subscribed:
            return await self.start(update, context)

        if text == "⬅️ العودة للقائمة الرئيسية":
            return await self.start(update, context)

        shamcash_data = data_manager.get_shamcash_data()
        address = shamcash_data.get('address')

        if text == "ليرة سورية (SYP)":
            context.user_data['shamcash_currency'] = 'SYP'
            message = f"💳 **شحن عبر شام كاش - ليرة سورية**\n\n"
            message += f"📋 **خطوات الشحن:**\n"
            message += f"1️⃣ قم بتحويل المبلغ المراد شحنه عبر شام كاش\n"
            message += f"2️⃣ استخدم العنوان التالي:\n\n"
            message += f"📮 `{address}`\n\n"
            message += f"3️⃣ بعد إتمام التحويل، أدخل رقم العملية:"

            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardRemove()
            )
            return ENTERING_SYRIATEL_TRANSACTION

        elif text == "دولار أمريكي (USD)":
            context.user_data['shamcash_currency'] = 'USD'
            exchange_rate = shamcash_data.get('exchange_rate', 3000)

            message = f"💳 **شحن عبر شام كاش - دولار أمريكي**\n\n"
            message += f"💱 **سعر الصرف:** 1 USD = {exchange_rate:,} SYP\n\n"
            message += f"📋 **خطوات الشحن:**\n"
            message += f"1️⃣ قم بتحويل المبلغ المراد إيداعه عبر شام كاش\n"
            message += f"2️⃣ استخدم العنوان التالي:\n\n"
            message += f"📮 `{address}`\n\n"
            message += f"3️⃣ بعد إتمام التحويل، أدخل رقم العملية:"

            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardRemove()
            )
            return ENTERING_SYRIATEL_TRANSACTION

        else:
            await update.message.reply_text("يرجى اختيار عملة صحيحة.")
            return SELECTING_SHAMCASH_CURRENCY

    async def handle_charge_code_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle charge code input"""
        charge_code = update.message.text.strip().upper()

        if not charge_code:
            await update.message.reply_text("يرجى إدخال كود شحن صحيح:")
            return ENTERING_CHARGE_CODE

        # Check if code exists and is valid
        code_value = data_manager.get_charge_code_value(charge_code)

        if code_value is None:
            await update.message.reply_text(
                "❌ كود الشحن غير صحيح أو تم استخدامه من قبل.\n"
                "يرجى التحقق من الكود والمحاولة مرة أخرى."
            )
            return await self.start(update, context)

        # Code is valid, add balance directly
        user = update.effective_user
        data_manager.update_user_balance(user.id, code_value)
        data_manager.use_charge_code(charge_code)

        # Send confirmation to user
        await update.message.reply_text(
            f"✅ **تم استخدام كود الشحن بنجاح!**\n\n"
            f"🏷️ الكود: `{charge_code}`\n"
            f"💰 القيمة المضافة: {code_value:,} SYP\n"
            f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"تم إضافة المبلغ إلى رصيدك مباشرة.",
            parse_mode='Markdown'
        )

        # Notify admin about code usage
        try:
            admin_message = f"🏷️ تم استخدام كود شحن\n\n"
            admin_message += f"👤 المستخدم: @{user.username or user.first_name} (`{user.id}`)\n"
            admin_message += f"🏷️ الكود: `{charge_code}`\n"
            admin_message += f"💰 القيمة: {code_value:,} SYP\n"
            admin_message += f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}"

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_message
            )
        except Exception as e:
            logger.error(f"Failed to notify admin about code usage: {e}")

        return await self.start(update, context)

    async def handle_syriatel_transaction_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle transaction number input for various payment methods"""
        transaction_number = update.message.text.strip()

        if not transaction_number:
            await update.message.reply_text("يرجى إدخال رقم العملية:")
            return ENTERING_SYRIATEL_TRANSACTION

        context.user_data['transaction_number'] = transaction_number
        payment_method = context.user_data.get('payment_method', 'syriatel')

        if payment_method == 'shamcash':
            shamcash_currency = context.user_data.get('shamcash_currency', 'SYP')
            if shamcash_currency == 'USD':
                amount_prompt = "أدخل المبلغ المرسل (USD):"
            else:
                amount_prompt = "أدخل قيمة المبلغ المرسل عبر شام كاش (SYP):"
        elif payment_method == 'payeer':
            amount_prompt = "أدخل المبلغ المرسل (Payeer USD):"
        elif payment_method == 'usdt_bep20':
            amount_prompt = "أدخل المبلغ المرسل (USDT):"
        else:  # syriatel
            method_name = "سيريتل كاش"
            amount_prompt = f"أدخل قيمة المبلغ المرسل عبر {method_name}:"

        await update.message.reply_text(amount_prompt)
        return ENTERING_SYRIATEL_AMOUNT

    async def handle_syriatel_amount_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle amount input for various payment methods"""
        payment_method = context.user_data.get('payment_method', 'syriatel')
        shamcash_currency = context.user_data.get('shamcash_currency', 'SYP')

        # For Payeer, USDT, and Sham Cash USD, ask for USD/USDT amount first
        if payment_method in ['payeer', 'usdt_bep20'] or (payment_method == 'shamcash' and shamcash_currency == 'USD'):
            try:
                usd_amount = float(update.message.text.strip())
                if usd_amount <= 0:
                    raise ValueError

                context.user_data['usd_amount'] = usd_amount
                transaction_number = context.user_data.get('transaction_number')

                if payment_method == 'payeer':
                    payeer_data = data_manager.get_payeer_data()
                    exchange_rate = payeer_data['exchange_rate']
                    syp_amount = int(usd_amount * exchange_rate)
                    method_name = "Payeer"
                    currency = "USD"
                elif payment_method == 'shamcash':
                    shamcash_data = data_manager.get_shamcash_data()
                    exchange_rate = shamcash_data['exchange_rate']
                    syp_amount = int(usd_amount * exchange_rate)
                    method_name = "شام كاش"
                    currency = "USD"
                else:  # usdt_bep20
                    usdt_data = data_manager.get_usdt_data()
                    exchange_rate = usdt_data['exchange_rate']
                    syp_amount = int(usd_amount * exchange_rate)
                    method_name = "USDT BEP-20"
                    currency = "USDT"

                context.user_data['charge_amount'] = syp_amount

                # Show confirmation
                message = f"💳 **شحن رصيد عبر {method_name}**\n\n"
                message += f"💱 المبلغ المرسل: {usd_amount} {currency}\n"
                message += f"💱 سعر الصرف: {exchange_rate:,} SYP/{currency}\n"
                message += f"💰 القيمة بالليرة السورية: {syp_amount:,} SYP\n"
                message += f"📱 رقم العملية: {transaction_number}\n\n"
                message += "هل تريد تأكيد الطلب؟"

                keyboard = [
                    [InlineKeyboardButton("✅ تأكيد الطلب", callback_data="confirm_charge_payment")],
                    [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_charge_payment")]
                ]

                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

                return CONFIRMING_SYRIATEL_PAYMENT

            except ValueError:
                if payment_method == 'payeer':
                    await update.message.reply_text("يرجى إدخال مبلغ صحيح بـ Payeer USD (رقم موجب):")
                elif payment_method == 'shamcash':
                    await update.message.reply_text("يرجى إدخال مبلغ صحيح بـ USD (رقم موجب):")
                else:
                    await update.message.reply_text("يرجى إدخال مبلغ صحيح بـ USDT (رقم موجب):")
                return ENTERING_SYRIATEL_AMOUNT

        # For traditional payment methods (Syriatel, Shamcash)
        else:
            try:
                amount = int(update.message.text.strip())
                if amount <= 0:
                    raise ValueError

                context.user_data['charge_amount'] = amount
                transaction_number = context.user_data.get('transaction_number')

                if payment_method == 'shamcash':
                    method_name = "شام كاش"
                elif payment_method == 'payeer':
                    method_name = "Payeer"
                elif payment_method == 'usdt_bep20':
                    method_name = "USDT BEP-20"
                else:
                    method_name = "سيريتل كاش"

                # Show confirmation
                message = f"💳 **شحن رصيد عبر {method_name}**\n\n"
                message += f"💰 القيمة: {amount:,} SYP\n"
                message += f"📱 رقم العملية: {transaction_number}\n\n"
                message += "هل تريد تأكيد الطلب؟"

                keyboard = [
                    [InlineKeyboardButton("✅ تأكيد الطلب", callback_data="confirm_charge_payment")],
                    [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_charge_payment")]
                ]

                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

                return CONFIRMING_SYRIATEL_PAYMENT

            except ValueError:
                await update.message.reply_text("يرجى إدخال مبلغ صحيح (رقم موجب):")
                return ENTERING_SYRIATEL_AMOUNT

    async def handle_syriatel_payment_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle Syriatel payment confirmation"""
        query = update.callback_query
        await query.answer()

        if query.data == "cancel_charge_payment":
            await query.edit_message_text("تم إلغاء طلب الشحن.")
            context.user_data.clear()
            return MAIN_MENU

        elif query.data == "confirm_charge_payment":
            user = update.effective_user
            amount = context.user_data.get('charge_amount')
            transaction_number = context.user_data.get('transaction_number')
            payment_method = context.user_data.get('payment_method', 'syriatel')

            method_name = "شام كاش" if payment_method == 'shamcash' else "سيريتل كاش"

            # Update user message to show processing
            if payment_method == 'shamcash':
                method_name = "شام كاش"
                processing_message = f"شحن رصيد عبر {method_name}\n\n"
                processing_message += f"💰 القيمة: {amount:,} SYP\n"
                processing_message += f"📱 رقم العملية: {transaction_number}\n\n"
                processing_message += "⏳ جاري معالجة الدفعة..."
            elif payment_method == 'payeer':
                method_name = "Payeer"
                usd_amount = context.user_data.get('usd_amount', 0)
                processing_message = f"شحن رصيد عبر {method_name}\n\n"
                processing_message += f"💱 المبلغ المرسل: {usd_amount} USD\n"
                processing_message += f"💰 القيمة بالليرة: {amount:,} SYP\n"
                processing_message += f"📱 رقم العملية: {transaction_number}\n\n"
                processing_message += "⏳ جاري معالجة الدفعة..."
            elif payment_method == 'usdt_bep20':
                method_name = "USDT BEP-20"
                usd_amount = context.user_data.get('usd_amount', 0)
                processing_message = f"شحن رصيد عبر {method_name}\n\n"
                processing_message += f"💱 المبلغ المرسل: {usd_amount} USDT\n"
                processing_message += f"💰 القيمة بالليرة: {amount:,} SYP\n"
                processing_message += f"📱 رقم العملية: {transaction_number}\n\n"
                processing_message += "⏳ جاري معالجة الدفعة..."
            else:  # syriatel
                method_name = "سيريتل كاش"
                processing_message = f"شحن رصيد عبر {method_name}\n\n"
                processing_message += f"💰 القيمة: {amount:,} SYP\n"
                processing_message += f"📱 رقم العملية: {transaction_number}\n\n"
                processing_message += "⏳ جاري معالجة الدفعة..."

            await query.edit_message_text(processing_message)

            # Send to admin with better error handling and multiple format attempts
            def escape_markdown_v2(text):
                special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
                for char in special_chars:
                    text = str(text).replace(char, f'\\{char}')
                return text

            keyboard = [
                [InlineKeyboardButton("✅ قبول", callback_data=f"approve_transfer_{user.id}_{amount}")],
                [InlineKeyboardButton("❌ رفض", callback_data=f"reject_transfer_{user.id}")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            # Send to balance requests channel first, then to admin as backup
            channel_sent = await self.send_balance_request_to_channel(context, user, amount, transaction_number, payment_method, reply_markup)

            # Also send to admin as backup if channel failed
            if not channel_sent:
                logger.warning(f"Failed to send to balance requests channel, sending to admin as backup")
                await self.send_balance_request_to_admin(context, user, amount, transaction_number, payment_method, reply_markup)

            context.user_data.clear()
            return MAIN_MENU

    async def handle_admin_charge_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin charge approval/rejection"""
        query = update.callback_query
        await query.answer()

        if not data_manager.is_user_admin(update.effective_user.id):
            return

        data_parts = query.data.split('_')

        if query.data.startswith("approve_transfer_"):
            user_id = int(data_parts[2])
            amount = int(data_parts[3])

            data_manager.update_user_balance(user_id, amount)

            # Get original message content and update status
            original_text = query.message.text
            updated_text = original_text.replace("⏳ الحالة: في انتظار المراجعة", "✅ الحالة: تم قبول الطلب")
            updated_text += f"\n\n✅ تم إضافة {amount:,} SYP لرصيد المستخدم"

            await query.edit_message_text(updated_text)

            # Notify user with correct method name
            try:
                # Extract transaction number from original message
                transaction_number = "غير محدد"
                if "رقم العملية:" in original_text:
                    try:
                        transaction_number = original_text.split("رقم العملية:")[1].split("\n")[0].strip()
                    except:
                        pass

                if 'Payeer' in original_text:
                    method_display = "Payeer"
                elif 'USDT BEP-20' in original_text:
                    method_display = "USDT BEP-20"
                elif 'شام كاش' in original_text:
                    method_display = "شام كاش"
                else:
                    method_display = "سيريتل كاش"

                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"✅ تم قبول طلب شحن الرصيد عبر {method_display}\n💰 تم إضافة {amount:,} SYP لرصيدك\n📱 رقم العملية: {transaction_number}"
                )
            except Exception as e:
                logger.error(f"Failed to notify user about transfer approval: {e}")

        elif query.data.startswith("reject_transfer_"):
            user_id = int(data_parts[2])

            # Get original message content and update status
            original_text = query.message.text
            updated_text = original_text.replace("⏳ الحالة: في انتظار المراجعة", "❌ الحالة: تم رفض الطلب")
            updated_text += "\n\n❌ سبب الرفض: لم يتم التحقق من صحة المعاملة"

            await query.edit_message_text(updated_text)

            # Notify user with correct method name
            try:
                # Extract transaction number from original message
                transaction_number = "غير محدد"
                if "رقم العملية:" in original_text:
                    try:
                        transaction_number = original_text.split("رقم العملية:")[1].split("\n")[0].strip()
                    except:
                        pass

                if 'Payeer' in original_text:
                    method_display = "Payeer"
                elif 'USDT BEP-20' in original_text:
                    method_display = "USDT BEP-20"
                elif 'شام كاش' in original_text:
                    method_display = "شام كاش"
                else:
                    method_display = "سيريتل كاش"

                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"❌ تم رفض طلب شحن الرصيد عبر {method_display}\n📱 رقم العملية: {transaction_number}\n\nيرجى التأكد من صحة البيانات أو التواصل مع الدعم."
                )
            except Exception as e:
                logger.error(f"Failed to notify user about transfer rejection: {e}")

        # Handle agent withdrawal requests
        elif query.data.startswith("transfer_to_balance_"):
            # Extract user_id and amount from callback data
            parts = query.data.split('_')
            user_id = int(parts[3])
            amount = int(parts[4])

            # Add amount to user's main balance
            data_manager.update_user_balance(user_id, amount)

            # Update admin message
            original_text = query.message.text
            updated_text = original_text.replace("⚠️ **تم تصفير أرباح الوكيل بالفعل**",
                                               f"✅ **تم تحويل {amount:,} SYP للرصيد الرئيسي**")

            await query.edit_message_text(updated_text, parse_mode='Markdown')

            # Notify agent
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"✅ **تم الموافقة على طلب السحب!**\n\n"
                         f"💰 تم تحويل {amount:,} SYP إلى رصيد حسابك الرئيسي\n"
                         f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to notify agent about balance transfer: {e}")

        elif query.data.startswith("approve_external_withdrawal_"):
            # Extract user_id and amount from callback data
            parts = query.data.split('_')
            user_id = int(parts[3])
            amount = int(parts[4])

            # Update admin message
            original_text = query.message.text
            updated_text = original_text.replace("⚠️ **تم تصفير أرباح الوكيل بالفعل**",
                                               f"✅ **تم الموافقة على السحب الخارجي {amount:,} SYP**")

            await query.edit_message_text(updated_text, parse_mode='Markdown')

            # Notify agent
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"✅ **تم الموافقة على طلب السحب الخارجي!**\n\n"
                         f"💸 المبلغ المعتمد للسحب: {amount:,} SYP\n"
                         f"📞 سيتم التواصل معك قريباً لتنفيذ العملية\n"
                         f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to notify agent about external withdrawal approval: {e}")

        elif query.data.startswith("reject_withdrawal_"):
            # Extract user_id and original amount from callback data
            parts = query.data.split('_')
            user_id = int(parts[2])
            original_amount = int(parts[3])

            # Return earnings to agent
            data_manager.add_agent_earnings(user_id, original_amount)

            # Update admin message
            original_text = query.message.text
            updated_text = original_text.replace("⚠️ **تم تصفير أرباح الوكيل بالفعل**",
                                               f"❌ **تم رفض الطلب وإرجاع {original_amount:,} SYP للوكيل**")

            await query.edit_message_text(updated_text, parse_mode='Markdown')

            # Notify agent
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"❌ **تم رفض طلب السحب**\n\n"
                         f"💰 تم إرجاع {original_amount:,} SYP إلى أرباحك\n"
                         f"📞 يرجى التواصل مع الإدارة للاستفسار\n"
                         f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to notify agent about withdrawal rejection: {e}")

    async def show_payments(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show available payment services for users"""
        payments = data_manager.get_payments()

        if not payments:
            await update.message.reply_text("لا توجد خدمات مدفوعات متاحة حالياً.")
            return MAIN_MENU

        message = "🌟 **خدمات المدفوعات المتاحة:**\n\n"

        keyboard = []
        for service_id, service_data in payments.items():
            message += f"🔹 {service_data['name']}\n"
            keyboard.append([InlineKeyboardButton(
                service_data['name'],
                callback_data=f"payment_service_{service_id}"
            )])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        return MAIN_MENU

    async def show_payments_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show payments management interface"""
        payments = data_manager.get_payments()

        message = "🌟 **إدارة خدمات المدفوعات**\n\nاختر العملية:"

        keyboard = [
            [KeyboardButton("عرض خدمات المدفوعات المتاحة 🌟")],
            [KeyboardButton("إضافة خدمة جديدة ➕")],
            [KeyboardButton("إدارة الفئات 🏷️")],
            [KeyboardButton("حذف خدمة مدفوعات 🗑️")],
            [KeyboardButton("تعديل/حذف خدمة 🗑️"), KeyboardButton("تعديل/حذف فئة ✏️")],
            [KeyboardButton("⬅️ العودة للوحة التحكم")]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        return MANAGING_PAYMENT_SERVICES

    async def handle_payments_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle payments management selection"""
        text = update.message.text

        if text == "عرض خدمات المدفوعات المتاحة 🌟":
            payments = data_manager.get_payments()
            if not payments:
                await update.message.reply_text("لا توجد خدمات مدفوعات متاحة حالياً.")
            else:
                message = "🌟 **خدمات المدفوعات المتاحة:**\n\n"
                for service_id, service_data in payments.items():
                    message += f"🔹 {service_data['name']} (ID: {service_id})\n"
                    for cat_id, cat_data in service_data.get('categories', {}).items():
                        if cat_data.get('pricing_type') == 'fixed' or 'type' not in cat_data:
                            price = cat_data.get('price', 0)
                            message += f"   • {cat_data['name']}: {price:,} SYP\n"
                        else:
                            price_per_unit = cat_data.get('price_per_unit', 0)
                            message += f"   • {cat_data['name']}: {price_per_unit:,} SYP/وحدة\n"
                    message += "\n"
                await update.message.reply_text(message, parse_mode='Markdown')
            return MANAGING_PAYMENT_SERVICES

        elif text == "إضافة خدمة جديدة ➕":
            await update.message.reply_text("أدخل اسم الخدمة الجديدة:")
            return ENTERING_SERVICE_NAME

        elif text == "حذف خدمة مدفوعات 🗑️":
            return await self.show_delete_payment_service_selection(update, context)

        elif text == "إدارة الفئات 🏷️":
            return await self.show_payment_categories_management(update, context)

        elif text == "تعديل/حذف خدمة 🗑️":
            return await self.show_payment_delete_action_selection(update, context, 'service')

        elif text == "تعديل/حذف فئة ✏️":
            return await self.show_payment_delete_action_selection(update, context, 'category')

        elif text == "⬅️ العودة للوحة التحكم":
            return await self.show_admin_panel(update, context)

        else:
            await update.message.reply_text("يرجى اختيار خيار صحيح من القائمة.")
            return MANAGING_PAYMENT_SERVICES

    async def handle_payment_name_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle payment service name entry"""
        payment_name = update.message.text.strip()

        if not payment_name:
            await update.message.reply_text("يرجى إدخال اسم صحيح للخدمة:")
            return ENTERING_PAYMENT_NAME

        context.user_data['payment_name'] = payment_name
        await update.message.reply_text("أدخل سعر الخدمة بـ SYP:")
        return ENTERING_PAYMENT_PRICE

    async def handle_payment_price_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle payment service price entry"""
        try:
            price = int(update.message.text.strip())
            if price <= 0:
                raise ValueError

            payment_name = context.user_data.get('payment_name')
            context.user_data['payment_price'] = price

            message = f"تأكيد إضافة خدمة المدفوعات:\n\n"
            message += f"الاسم: {payment_name}\n"
            message += f"السعر: {price:,} SYP\n\n"
            message += "هل تريد إضافة هذه الخدمة؟"

            keyboard = [
                [InlineKeyboardButton("✅ إضافة", callback_data="confirm_add_payment")],
                [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_payment")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup)
            return CONFIRMING_PAYMENT_ADD

        except ValueError:
            await update.message.reply_text("يرجى إدخال سعر صحيح (رقم موجب):")
            return ENTERING_PAYMENT_PRICE

    async def handle_payment_add_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle payment addition confirmation"""
        query = update.callback_query
        await query.answer()

        if query.data == "cancel_add_payment":
            await query.edit_message_text("تم إلغاء إضافة الخدمة.")
            context.user_data.clear()
            return await self.show_payments_management(update, context)

        elif query.data == "confirm_add_payment":
            payment_name = context.user_data.get('payment_name')
            payment_price = context.user_data.get('payment_price')

            # Generate service ID
            service_id = payment_name.lower().replace(" ", "_").replace("-", "_")

            # Add to database
            data_manager.add_payment_service(service_id, payment_name, payment_price)

            await query.edit_message_text(f"✅ تم إضافة خدمة '{payment_name}' بنجاح!")
            context.user_data.clear()
            return MANAGING_PAYMENTS

    async def handle_payment_deletion_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle payment service deletion selection"""
        text = update.message.text

        if text == "⬅️ العودة":
            return await self.show_payments_management(update, context)

        # Extract service name from text (remove category count)
        service_name = text.split(" (")[0] if " (" in text else text

        # Find selected payment
        payments = data_manager.get_payments()
        selected_payment_id = None
        selected_payment_name = None
        categories_count = 0

        for payment_id, payment_data in payments.items():
            if payment_data['name'] == service_name:
                selected_payment_id = payment_id
                selected_payment_name = payment_data['name']
                categories_count = len(payment_data.get('categories', {}))
                break

        if not selected_payment_id:
            await update.message.reply_text("يرجى اختيار خدمة من القائمة.")
            return SELECTING_PAYMENT_TO_DELETE

        context.user_data['delete_payment_id'] = selected_payment_id
        context.user_data['delete_payment_name'] = selected_payment_name

        message = f"⚠️ **تأكيد حذف الخدمة**\n\n"
        message += f"الخدمة: **{selected_payment_name}**\n"
        message += f"عدد الفئات: **{categories_count}**\n\n"
        message += f"⚠️ **سيتم حذف الخدمة بالكامل مع جميع فئاتها!**\n"
        message += f"هذا الإجراء لا يمكن التراجع عنه!\n\n"
        message += f"هل أنت متأكد من حذف هذه الخدمة؟"

        keyboard = [
            [KeyboardButton("✅ تأكيد الحذف")],
            [KeyboardButton("❌ إلغاء")]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        return CONFIRMING_PAYMENT_DELETE

    async def handle_payment_delete_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle payment deletion confirmation"""
        text = update.message.text

        if text == "✅ تأكيد الحذف":
            payment_id = context.user_data.get('delete_payment_id')
            payment_name = context.user_data.get('delete_payment_name')

            success = data_manager.delete_payment_service(payment_id)

            if success:
                await update.message.reply_text(f"✅ تم حذف خدمة '{payment_name}' بنجاح!")
            else:
                await update.message.reply_text("❌ حدث خطأ في عملية الحذف.")

            context.user_data.clear()
            return await self.show_payments_management(update, context)

        elif text == "❌ إلغاء":
            await update.message.reply_text("تم إلغاء عملية الحذف.")
            context.user_data.clear()
            return await self.show_payments_management(update, context)

        else:
            await update.message.reply_text("يرجى اختيار تأكيد الحذف أو الإلغاء.")
            return CONFIRMING_PAYMENT_DELETE

    async def show_delete_payment_service_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show delete payment service selection"""
        payments = data_manager.get_payments()

        if not payments:
            await update.message.reply_text("لا توجد خدمات مدفوعات متاحة للحذف.")
            return await self.show_payments_management(update, context)

        message = "🗑️ **حذف خدمة مدفوعات**\n\nاختر الخدمة المراد حذفها:"
        keyboard = []

        for service_id, service_data in payments.items():
            categories_count = len(service_data.get('categories', {}))
            button_text = f"{service_data['name']} ({categories_count} فئة)"
            keyboard.append([KeyboardButton(button_text)])

        keyboard.append([KeyboardButton("⬅️ العودة")])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return SELECTING_PAYMENT_TO_DELETE

    async def show_payment_categories_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show payment categories management interface"""
        payments = data_manager.get_payments()

        if not payments:
            await update.message.reply_text("لا توجد خدمات مدفوعات متاحة. يرجى إضافة خدمة أولاً.")
            return await self.show_payments_management(update, context)

        message = "🏷️ **إدارة فئات المدفوعات**\n\nاختر الخدمة:"
        keyboard = []
        for service_id, service_data in payments.items():
            keyboard.append([KeyboardButton(service_data['name'])])
        keyboard.append([KeyboardButton("⬅️ العودة")])

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return SELECTING_CATEGORY_APP

    async def show_payment_delete_action_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, item_type: str) -> int:
        """Show payment delete action selection"""
        context.user_data['delete_item_type'] = item_type

        if item_type == 'service':
            message = "🗑️ **حذف/تعديل خدمات المدفوعات**\n\nاختر العملية:"
        else:
            message = "✏️ **حذف/تعديل فئات المدفوعات**\n\nاختر العملية:"

        keyboard = [
            [KeyboardButton("حذف 🗑️")],
            [KeyboardButton("تعديل ✏️")],
            [KeyboardButton("⬅️ العودة")]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return SELECTING_DELETE_ACTION

    async def handle_service_name_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle service name entry"""
        service_name = update.message.text.strip()

        if not service_name:
            await update.message.reply_text("يرجى إدخال اسم صحيح للخدمة:")
            return ENTERING_SERVICE_NAME

        # Generate service ID from name
        service_id = service_name.lower().replace(" ", "_").replace("-", "_")

        # Add to database
        data_manager.add_payment_service(service_id, service_name)

        await update.message.reply_text(f"✅ تم إضافة خدمة '{service_name}' بنجاح!")

        return await self.show_payments_management(update, context)

    async def handle_category_name_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle category name entry"""
        category_name = update.message.text.strip()

        if not category_name:
            await update.message.reply_text("يرجى إدخال اسم صحيح للفئة:")
            return ENTERING_CATEGORY_NAME

        context.user_data['category_name'] = category_name
        context.user_data['category_id'] = category_name.lower().replace(" ", "_")

        await update.message.reply_text("أدخل سعر هذه الفئة بـ SYP:")
        return ENTERING_CATEGORY_PRICE

    async def handle_category_price_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle category price entry"""
        try:
            price = int(update.message.text.strip())
            if price <= 0:
                raise ValueError

            context.user_data['category_price'] = price
            service_type = context.user_data.get('category_service_type')
            pricing_type = context.user_data.get('category_pricing_type', 'fixed')

            # For apps and games with fixed pricing, add category directly
            if service_type in ['app', 'game'] and pricing_type == 'fixed':
                category_name = context.user_data.get('quantity_category_name')
                app_id = context.user_data.get('selected_app_for_category')
                category_id = category_name.lower().replace(" ", "_")

                category_data = {
                    "name": category_name,
                    "price": price,
                    "type": "fixed"
                }

                data_manager.add_category(service_type, app_id, category_id, category_data)

                await update.message.reply_text(f"✅ تم إضافة فئة '{category_name}' بنجاح!\n💰 السعر: {price:,} SYP")
                return await self.show_categories_management(update, context)

            # For payment services with fixed pricing, add directly without asking for input type
            elif service_type not in ['app', 'game'] and pricing_type == 'fixed':
                category_name = context.user_data.get('quantity_category_name')
                service_id = context.user_data.get('selected_app_for_category')
                category_id = category_name.lower().replace(" ", "_")

                # Create category data without input type (set to none by default)
                category_data = {
                    "name": category_name,
                    "price": price,
                    "type": "fixed",
                    "input_type": "none",
                    "input_label": "",
                    "pricing_type": "fixed"
                }

                # Add category to service
                success = data_manager.add_payment_category(service_id, category_id, category_data)

                if success:
                    await update.message.reply_text(f"✅ تم إضافة فئة '{category_name}' بنجاح!\n💰 السعر الثابت: {price:,} SYP")
                    # Clear category-specific data
                    for key in ['quantity_category_name', 'category_price', 'category_pricing_type']:
                        context.user_data.pop(key, None)
                    return await self.show_payments_management(update, context)
                else:
                    await update.message.reply_text("❌ حدث خطأ في إضافة الفئة.")
                    return await self.show_payments_management(update, context)
            else:
                # For apps/games with quantity pricing, go to min order entry
                await update.message.reply_text("أدخل أقل طلب:")
                return ENTERING_MIN_ORDER

        except ValueError:
            await update.message.reply_text("يرجى إدخال سعر صحيح (رقم موجب):")
            return ENTERING_CATEGORY_PRICE

    async def handle_payment_category_type_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle payment category type selection - for payment services only"""
        text = update.message.text

        if text == "⬅️ إلغاء":
            await update.message.reply_text("تم إلغاء إضافة الفئة.")
            return await self.show_payments_management(update, context)

        if text == "فئة ثابتة 💰":
            context.user_data['category_pricing_type'] = 'fixed'
            message = "اختر نوع البيانات المطلوبة من المستخدم لهذه الفئة:"

            keyboard = [
                [KeyboardButton("عنوان بريد إلكتروني 📧")],
                [KeyboardButton("رقم هاتف 📱")],
                [KeyboardButton("عنوان محفظة 💳")],
                [KeyboardButton("لا يتطلب بيانات إضافية ✅")],
                [KeyboardButton("⬅️ إلغاء")]
            ]

            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(message, reply_markup=reply_markup)
            return SELECTING_CATEGORY_INPUT_TYPE

        elif text == "فئة حسب الكمية 📊":
            context.user_data['category_pricing_type'] = 'quantity'
            await update.message.reply_text("أدخل أقل طلب مسموح:")
            return ENTERING_MIN_ORDER

        else:
            await update.message.reply_text("يرجى اختيار نوع التسعير من القائمة.")
            return SELECTING_CATEGORY_TYPE

    async def handle_category_input_type_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle category input type selection - REMOVED"""
        # This function has been removed as input type selection is no longer needed
        await update.message.reply_text("❌ حدث خطأ في النظام.")
        return await self.show_payments_management(update, context)

    async def handle_category_add_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle category addition confirmation"""
        query = update.callback_query
        await query.answer()

        if query.data == "add_another_category":
            await query.edit_message_text("أدخل اسم الفئة الجديدة:")
            return ENTERING_CATEGORY_NAME

        elif query.data == "finish_adding_categories":
            service_name = context.user_data['service_name']
            await query.edit_message_text(f"✅ تم إنشاء خدمة '{service_name}' بنجاح مع جميع فئاتها!")
            context.user_data.clear()
            return MANAGING_PAYMENT_SERVICES

    async def handle_service_selection_for_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle service selection for editing"""
        text = update.message.text

        if text == "⬅️ العودة":
            return await self.show_payments_management(update, context)

        # Extract service name from text (remove category count)
        service_name = text.split(" (")[0] if " (" in text else text

        # Find selected service
        payments = data_manager.get_payments()
        selected_service_id = None

        for service_id, service_data in payments.items():
            if service_data['name'] == service_name:
                selected_service_id = service_id
                break

        if not selected_service_id:
            await update.message.reply_text("يرجى اختيار خدمة من القائمة.")
            return SELECTING_SERVICE_TO_EDIT

        context.user_data['editing_service_id'] = selected_service_id
        service_data = payments[selected_service_id]

        message = f"📋 **إدارة خدمة: {service_data['name']}**\n\n"

        if service_data.get('categories'):
            message += "**الفئات الحالية:**\n"
            for cat_id, cat_data in service_data['categories'].items():
                input_desc = ""
                if cat_data['input_type'] == 'email':
                    input_desc = " 📧"
                elif cat_data['input_type'] == 'phone':
                    input_desc = " 📱"
                elif cat_data['input_type'] == 'wallet':
                    input_desc = " 💳"
                elif cat_data['input_type'] == 'none':
                    input_desc = " ✅"

                pricing_type = cat_data.get('pricing_type', 'fixed')
                if pricing_type == 'fixed':
                    price_text = f"{cat_data['price']:,} SYP"
                else:
                    price_text = f"{cat_data['price_per_unit']:,} SYP/وحدة"

                message += f"• **{cat_data['name']}**: {price_text}{input_desc}\n"
            message += "\n"
        else:
            message += "لا توجد فئات بعد.\n\n"

        message += "اختر العملية:"

        keyboard = [
            [KeyboardButton("إضافة فئة جديدة ➕")],
            [KeyboardButton("حذف فئة 🗑️"), KeyboardButton("تعديل فئة ✏️")],
            [KeyboardButton("⬅️ العودة")]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        return ADDING_SERVICE_CATEGORIES

    async def handle_service_categories_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle service categories management"""
        text = update.message.text

        if text == "إضافة فئة جديدة ➕":
            await update.message.reply_text("أدخل اسم الفئة الجديدة:")
            return ENTERING_CATEGORY_NAME

        elif text == "حذف فئة 🗑️":
            service_id = context.user_data.get('editing_service_id')
            if not service_id:
                await update.message.reply_text("خطأ: لم يتم تحديد الخدمة.")
                return await self.show_payments_management(update, context)

            payments = data_manager.get_payments()
            service_data = payments.get(service_id)

            if not service_data or not service_data.get('categories'):
                await update.message.reply_text("لا توجد فئات للحذف في هذه الخدمة.")
                return ADDING_SERVICE_CATEGORIES

            message = "⚠️ **حذف فئة**\n\nاختر الفئة المراد حذفها:"
            keyboard = []

            for cat_id, cat_data in service_data['categories'].items():
                keyboard.append([KeyboardButton(cat_data['name'])])

            keyboard.append([KeyboardButton("⬅️ إلغاء")])
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            return SELECTING_CATEGORY_TO_DELETE

        elif text == "تعديل فئة ✏️":
            service_id = context.user_data.get('editing_service_id')
            if not service_id:
                await update.message.reply_text("خطأ: لم يتم تحديد الخدمة.")
                return await self.show_payments_management(update, context)

            payments = data_manager.get_payments()
            service_data = payments.get(service_id)

            if not service_data or not service_data.get('categories'):
                await update.message.reply_text("لا توجد فئات للتعديل في هذه الخدمة.")
                return ADDING_SERVICE_CATEGORIES

            message = "✏️ **تعديل فئة**\n\nاختر الفئة المراد تعديلها:"
            keyboard = []

            for cat_id, cat_data in service_data['categories'].items():
                pricing_type = cat_data.get('pricing_type', 'fixed')
                if pricing_type == 'fixed':
                    price_text = f"{cat_data['price']:,} SYP"
                else:
                    price_text = f"{cat_data['price_per_unit']:,} SYP/وحدة"
                keyboard.append([KeyboardButton(f"{cat_data['name']} - {price_text}")])

            keyboard.append([KeyboardButton("⬅️ إلغاء")])
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            return SELECTING_CATEGORY_TO_EDIT

        elif text == "⬅️ العودة":
            context.user_data.pop('editing_service_id', None)
            return await self.show_payments_management(update, context)

        else:
            await update.message.reply_text("يرجى اختيار عملية صحيحة من القائمة.")
            return ADDING_SERVICE_CATEGORIES

    async def handle_broadcast_message_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle broadcast message entry"""
        message_text = update.message.text

        if not message_text or len(message_text.strip()) == 0:
            await update.message.reply_text("يرجى إدخال رسالة صحيحة:")
            return ENTERING_BROADCAST_MESSAGE

        context.user_data['broadcast_message'] = message_text

        # Show preview
        preview_message = f"📢 **معاينة الإذاعة:**\n\n{message_text}\n\n"
        preview_message += "هل تريد إرسال هذه الرسالة لجميع المستخدمين؟"

        keyboard = [
            [InlineKeyboardButton("✅ إرسال الإذاعة", callback_data="confirm_broadcast")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_broadcast")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(preview_message, reply_markup=reply_markup, parse_mode='Markdown')
        return CONFIRMING_BROADCAST

    async def handle_broadcast_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle broadcast confirmation"""
        query = update.callback_query
        await query.answer()

        if query.data == "cancel_broadcast":
            await query.edit_message_text("تم إلغاء الإذاعة.")
            context.user_data.clear()
            return await self.show_admin_panel(update, context)

        elif query.data == "confirm_broadcast":
            broadcast_message = context.user_data.get('broadcast_message')

            # Get all users
            all_users = data_manager.get_all_users()

            if not all_users:
                await query.edit_message_text("❌ لا يوجد مستخدمون لإرسال الإذاعة إليهم.")
                context.user_data.clear()
                return ADMIN_PANEL

            # Start broadcasting
            await query.edit_message_text("📢 جاري إرسال الإذاعة...")

            success_count = 0
            failed_count = 0

            for user_id in all_users.keys():
                try:
                    await context.bot.send_message(
                        chat_id=int(user_id),
                        text=broadcast_message,
                        parse_mode='Markdown'
                    )
                    success_count += 1
                    await asyncio.sleep(0.1)  # Small delay to avoid rate limits
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to send broadcast to {user_id}: {e}")

            # Send final report
            report_message = f"📊 **تقرير الإذاعة:**\n\n"
            report_message += f"✅ تم الإرسال بنجاح: {success_count}\n"
            report_message += f"❌ فشل الإرسال: {failed_count}\n"
            report_message += f"📈 إجمالي المستخدمين: {len(all_users)}"

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=report_message,
                parse_mode='Markdown'
            )

            context.user_data.clear()
            return ADMIN_PANEL

    async def show_bot_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show bot settings"""
        bot_enabled = data_manager.is_bot_enabled()
        status_text = "🟢 مُفعّل" if bot_enabled else "🔴 متوقف"

        message = f"⚙️ **إعدادات البوت**\n\n"
        message += f"حالة البوت: {status_text}\n\n"
        message += "اختر العملية:"

        keyboard = []
        if bot_enabled:
            keyboard.append([KeyboardButton("إيقاف البوت 🔴")])
        else:
            keyboard.append([KeyboardButton("تشغيل البوت 🟢")])

        keyboard.append([KeyboardButton("⬅️ العودة للوحة التحكم")])

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        return BOT_SETTINGS

    async def handle_admin_payment_order_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin actions on payment orders"""
        query = update.callback_query
        await query.answer()

        if not data_manager.is_user_admin(update.effective_user.id):
            return

        action, order_id = query.data.split('_', 3)[0], query.data.split('_', 3)[3]

        # Get order details
        orders = data_manager._load_json(data_manager.orders_file)
        order = orders.get(order_id)

        if not order:
            await query.edit_message_text("❌ الطلب غير موجود")
            return

        if action == "complete":
            data_manager.update_order_status(order_id, "مكتمل وتم الشحن بنجاح")

            # Update admin message without markdown to avoid parsing errors
            original_text = query.message.text
            updated_text = original_text.replace("📊 الحالة: قيد المعالجة", "📊 الحالة: مكتمل وتم الشحن بنجاح ✅")
            updated_text += f"\n\n✅ تم تنفيذ الطلب بواسطة الإدارة"

            await query.edit_message_text(updated_text)

            # Notify user
            try:
                user_message = f"✅ **تم شحن طلب الخدمة بنجاح!**\n\n"
                user_message += f"📱 القسم: مدفوعات\n\n"
                user_message += f"🎮 الخدمة: {order['service_name']}\n\n"
                user_message += f"🏷️ الفئة: {order['category_name']}\n\n"

                if order.get('pricing_type') == 'quantity':
                    user_message += f"📊 الكمية: {order.get('quantity', 1)}\n\n"

                user_message += f"💰 المبلغ: {order['price']:,.2f} SYP\n\n"

                if order['input_type'] != 'none' and order.get('input_data'):
                    user_message += f"📝 البيانات المرسلة: {order['input_data']}\n\n"

                user_message += f"🆔 رقم الطلب: {order_id}\n\n"
                user_message += f"📅 التاريخ: {order['timestamp']}\n\n"
                user_message += f"📊 الحالة: مكتمل وتم الشحن بنجاح ✅\n\n"
                user_message += f"شكراً لك لاستخدام خدماتنا! 💜"

                await context.bot.send_message(
                    chat_id=order['user_id'],
                    text=user_message,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to notify user about order completion: {e}")

        elif action == "reject":
            # Refund user balance
            data_manager.update_user_balance(order['user_id'], order['price'])
            data_manager.update_order_status(order_id, "مرفوض ولم تكتمل العملية")

            # Update admin message without markdown to avoid parsing errors
            original_text = query.message.text
            updated_text = original_text.replace("📊 الحالة: قيد المعالجة", "📊 الحالة: مرفوض ولم تكتمل العملية ❌")
            updated_text += f"\n\n❌ تم رفض الطلب وإرجاع المبلغ للعميل"

            await query.edit_message_text(updated_text)

            # Notify user
            try:
                user_message = f"❌ **تم رفض طلب الخدمة ولم تكتمل العملية**\n\n"
                user_message += f"📱 القسم: مدفوعات\n\n"
                user_message += f"🎮 الخدمة: {order['service_name']}\n\n"
                user_message += f"🏷️ الفئة: {order['category_name']}\n\n"

                if order.get('pricing_type') == 'quantity':
                    user_message += f"📊 الكمية: {order.get('quantity', 1)}\n\n"

                user_message += f"💰 المبلغ: {order['price']:,.2f} SYP\n\n"
                user_message += f"🆔 رقم الطلب: {order_id}\n\n"
                user_message += f"📅 التاريخ: {order['timestamp']}\n\n"
                user_message += f"📊 الحالة: مرفوض ولم تكتمل العملية ❌\n\n"
                user_message += f"💰 تم إرجاع {order['price']:,.2f} SYP لرصيدك\n\n"
                user_message += f"يرجى التواصل مع الدعم للاستفسار عن سبب الرفض"

                await context.bot.send_message(
                    chat_id=order['user_id'],
                    text=user_message,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to notify user about order rejection: {e}")

    async def handle_bot_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle bot settings selection"""
        text = update.message.text

        if text == "إيقاف البوت 🔴":
            data_manager.set_bot_enabled(False)
            await update.message.reply_text("🔴 تم إيقاف البوت. المستخدمون العاديون لن يتمكنوا من استخدامه.")
            return await self.show_bot_settings(update, context)

        elif text == "تشغيل البوت 🟢":
            data_manager.set_bot_enabled(True)
            await update.message.reply_text("🟢 تم تشغيل البوت. يمكن للمستخدمين الآن استخدامه بشكل طبيعي.")
            return await self.show_bot_settings(update, context)

        elif text == "⬅️ العودة للوحة التحكم":
            return await self.show_admin_panel(update, context)

        else:
            await update.message.reply_text("يرجى اختيار خيار صحيح من القائمة.")
            return BOT_SETTINGS

    async def handle_payment_service_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle payment service selection"""
        query = update.callback_query
        await query.answer()

        if query.data == "back_to_main":
            # Clear user data and return to main menu
            context.user_data.clear()

            # Delete the current message
            try:
                await query.delete_message()
            except Exception:
                pass

            # Get user info and show main menu
            user_id = update.effective_user.id
            user = data_manager.get_user(user_id)
            bot_name = data_manager.get_bot_name(english=False)

            welcome_text = f"""🎮 أهلاً بك في متجر {bot_name} 💰
أسرع منصة للشحن الإلكتروني في سوريا 🇸🇾
──────────────────────────
💳 معرفك: `{user_id}`
💵 رصيدك: **{user['balance']:,.2f} SYP**"""

            # Create keyboard
            keyboard = [
                [KeyboardButton("شحن تطبيق 📱"), KeyboardButton("شحن لعبة 🎮")],
                [KeyboardButton("شحن رصيد حسابك ➕"), KeyboardButton("تواصل مع الدعم 💬")]
            ]

            # Add referral button if system is enabled
            referral_settings = data_manager.get_referral_settings()
            if referral_settings["enabled"]:
                keyboard.append([KeyboardButton("نظام الإحالة 🎁")])

            # Add admin panel for all admins
            if data_manager.is_user_admin(user_id):
                keyboard.append([KeyboardButton("لوحة التحكم 🛠")])

            # Add ADMG01C panel for special admin
            if ADMG01C > 0 and user_id == ADMG01C:
                keyboard.append([KeyboardButton("ADMG01C ⚙️")])

            # Add agent panel for agents
            agent_data = data_manager.get_agent_by_user_id(user_id)
            if agent_data:
                keyboard.append([KeyboardButton("لوحة الوكيل 🤝")])

            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

            inline_keyboard = [[InlineKeyboardButton("📊 بياناتي", callback_data="show_my_statistics")]]
            inline_markup = InlineKeyboardMarkup(inline_keyboard)

            await query.message.reply_text(
                welcome_text,
                reply_markup=inline_markup,
                parse_mode='Markdown'
            )

            await query.message.reply_text(
                "اختر خدمة:",
                reply_markup=reply_markup
            )

            return MAIN_MENU

        service_id = query.data.replace("payment_service_", "")
        payments = data_manager.get_payments()

        service_data = payments.get(service_id)
        if not service_data:
            await query.edit_message_text("❌ الخدمة غير متاحة.")
            return MAIN_MENU

        # Clear previous selections and set new service
        context.user_data.clear()
        context.user_data['selected_payment_service'] = service_id

        # Show categories
        categories = service_data.get('categories', {})
        if not categories:
            await query.edit_message_text("❌ لا توجد فئات متاحة لهذه الخدمة.")
            return MAIN_MENU

        message = f"🌟 **{service_data['name']}**\n\nاختر الفئة:\n\n"

        keyboard = []
        for cat_id, cat_data in categories.items():
            input_desc = ""
            if cat_data['input_type'] == 'email':
                input_desc = " 📧"
            elif cat_data['input_type'] == 'phone':
                input_desc = " 📱"
            elif cat_data['input_type'] == 'wallet':
                input_desc = " 💳"

            # Check pricing type
            pricing_type = cat_data.get('pricing_type', 'fixed')

            if pricing_type == 'fixed':
                price_text = f"{cat_data['price']:,} SYP"
            else:
                price_text = f"{cat_data['price_per_unit']:,} SYP/وحدة"

            button_text = f"{cat_data['name']} - {price_text}{input_desc}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"payment_category_{cat_id}")])

        keyboard.append([InlineKeyboardButton("⬅️ العودة", callback_data="back_to_payments")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        return MAIN_MENU

    async def handle_payment_category_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle payment category selection"""
        query = update.callback_query
        await query.answer()

        if query.data == "back_to_payments":
            context.user_data.clear()
            return await self.show_payments(update, context)

        category_id = query.data.replace("payment_category_", "")
        service_id = context.user_data.get('selected_payment_service')

        if not service_id:
            await query.edit_message_text("❌ خطأ في النظام. يرجى المحاولة مرة أخرى.")
            return MAIN_MENU

        payments = data_manager.get_payments()
        service_data = payments.get(service_id)

        if not service_data:
            await query.edit_message_text("❌ الخدمة غير متاحة.")
            return MAIN_MENU

        category_data = service_data['categories'].get(category_id)

        if not category_data:
            await query.edit_message_text("❌ الفئة غير متاحة.")
            return MAIN_MENU

        context.user_data['selected_payment_category'] = category_id

        user = update.effective_user
        user_data = data_manager.get_user(user.id)

        pricing_type = category_data.get('pricing_type', 'fixed')

        # Check if it's quantity-based pricing
        if pricing_type == 'quantity':
            price_per_unit = category_data['price_per_unit']
            min_order = category_data.get('min_order', 1)
            max_order = category_data.get('max_order')

            context.user_data['price_per_unit'] = price_per_unit

            message = f"📱 **القسم:** مدفوعات\n\n"
            message += f"🌟 **الخدمة:** {service_data['name']}\n\n"
            message += f"🏷️ **الفئة:** {category_data['name']}\n\n"
            message += f"💰 **السعر لكل وحدة:** {price_per_unit:,} SYP\n\n"

            if min_order:
                message += f"📊 **أقل طلب:** {min_order}\n\n"
            if max_order:
                message += f"📊 **أقصى طلب:** {max_order}\n\n"

            message += "📊 **أدخل الكمية المطلوبة:**"

            await query.edit_message_text(message, parse_mode='Markdown')
            return ENTERING_QUANTITY

        # Fixed pricing
        else:
            category_price = category_data.get('price', 0)
            context.user_data['final_price'] = category_price
            context.user_data['quantity'] = 1

            # Check if input is required
            if category_data.get('input_type', 'none') == 'none':
                # No input required, ask for account ID
                await query.edit_message_text(
                    f"🌟 **{service_data['name']} - {category_data['name']}**\n\n"
                    f"💰 السعر: {category_price:,} SYP\n\n"
                    f"👤 يرجى إدخال معرف الحساب المراد الدفع إليه:"
                )
                return ENTERING_ACCOUNT_ID
            else:
                # Input required first
                input_label = category_data.get('input_label', 'البيانات المطلوبة')
                await query.edit_message_text(
                    f"🌟 **{service_data['name']} - {category_data['name']}**\n\n"
                    f"💰 السعر: {category_price:,} SYP\n\n"
                    f"📝 يرجى إدخال {input_label}:"
                )
                return ENTERING_PAYMENT_INPUT_DATA

    async def handle_payment_quantity_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle quantity input for quantity-based payment services"""
        try:
            quantity = float(update.message.text)
            if quantity <= 0:
                raise ValueError

            # Get category data to check min/max limits
            service_id = context.user_data.get('selected_payment_service')
            category_id = context.user_data.get('selected_payment_category')

            payments = data_manager.get_payments()
            service_data = payments.get(service_id)

            if not service_data:
                await update.message.reply_text("❌ خطأ: الخدمة غير موجودة.")
                return MAIN_MENU

            category_data = service_data['categories'].get(category_id)

            if not category_data:
                await update.message.reply_text("❌ خطأ: الفئة غير موجودة.")
                return MAIN_MENU

            # Check min/max order limits
            min_order = category_data.get('min_order')
            max_order = category_data.get('max_order')

            if min_order and quantity < min_order:
                await update.message.reply_text(f"أقل طلب مسموح: {min_order}. يرجى إدخال كمية أكبر:")
                return ENTERING_QUANTITY

            if max_order and quantity > max_order:
                await update.message.reply_text(f"أقصى طلب مسموح: {max_order}. يرجى إدخال كمية أقل:")
                return ENTERING_QUANTITY

            price_per_unit = context.user_data.get('price_per_unit', category_data.get('price_per_unit', 0))
            total_price = quantity * price_per_unit

            context.user_data['quantity'] = quantity
            context.user_data['final_price'] = total_price

            # Check if input is required
            if category_data.get('input_type', 'none') == 'none':
                # No input required, ask for account ID
                message = f"📱 **القسم:** مدفوعات\n\n"
                message += f"🌟 **الخدمة:** {service_data['name']}\n\n"
                message += f"🏷️ **الفئة:** {category_data['name']}\n\n"
                message += f"💰 **السعر لكل وحدة:** {price_per_unit:,} SYP\n\n"
                message += f"📊 **الكمية:** {quantity}\n\n"
                message += f"💰 **السعر الإجمالي:** {total_price:,.2f} SYP\n\n"
                message += f"👤 **يرجى إدخال معرف الحساب المراد الدفع إليه:**"

                await update.message.reply_text(message, parse_mode='Markdown')
                return ENTERING_ACCOUNT_ID
            else:
                # Input required, ask for it first
                input_label = category_data.get('input_label', 'البيانات المطلوبة')
                message = f"📱 **القسم:** مدفوعات\n\n"
                message += f"🌟 **الخدمة:** {service_data['name']}\n\n"
                message += f"🏷️ **الفئة:** {category_data['name']}\n\n"
                message += f"💰 **السعر لكل وحدة:** {price_per_unit:,} SYP\n\n"
                message += f"📊 **الكمية:** {quantity}\n\n"
                message += f"💰 **السعر الإجمالي:** {total_price:,.2f} SYP\n\n"
                message += f"📝 **يرجى إدخال {input_label}:**"

                await update.message.reply_text(message, parse_mode='Markdown')
                return ENTERING_PAYMENT_INPUT_DATA

        except ValueError:
            await update.message.reply_text("يرجى إدخال كمية صحيحة (رقم موجب):")
            return ENTERING_QUANTITY

    async def handle_payment_input_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle payment input data entry"""
        input_data = update.message.text.strip()

        # Get service and category data for validation
        service_id = context.user_data.get('selected_payment_service')
        category_id = context.user_data.get('selected_payment_category')

        if not service_id or not category_id:
            await update.message.reply_text("❌ خطأ في النظام. يرجى المحاولة مرة أخرى.")
            return await self.start(update, context)

        payments = data_manager.get_payments()
        service_data = payments.get(service_id)

        if not service_data:
            await update.message.reply_text("❌ الخدمة غير متاحة.")
            return await self.start(update, context)

        category_data = service_data['categories'].get(category_id)

        if not category_data:
            await update.message.reply_text("❌ الفئة غير متاحة.")
            return await self.start(update, context)

        if not input_data:
            await update.message.reply_text(f"يرجى إدخال {category_data['input_label']} صحيح:")
            return ENTERING_PAYMENT_INPUT_DATA

        # Basic validation based on input type
        if category_data['input_type'] == 'email':
            if '@' not in input_data or '.' not in input_data:
                await update.message.reply_text("يرجى إدخال عنوان بريد إلكتروني صحيح:")
                return ENTERING_PAYMENT_INPUT_DATA
        elif category_data['input_type'] == 'phone':
            # Remove spaces and special characters for basic validation
            phone_digits = ''.join(filter(str.isdigit, input_data))
            if len(phone_digits) < 8:
                await update.message.reply_text("يرجى إدخال رقم هاتف صحيح:")
                return ENTERING_PAYMENT_INPUT_DATA

        # Store the validated input data
        context.user_data['payment_input_data'] = input_data

        # Now ask for account ID
        pricing_type = category_data.get('pricing_type', 'fixed')
        quantity = context.user_data.get('quantity', 1)

        message = f"📱 **القسم:** مدفوعات\n\n"
        message += f"🌟 **الخدمة:** {service_data['name']}\n\n"
        message += f"🏷️ **الفئة:** {category_data['name']}\n\n"

        if pricing_type == 'quantity':
            price_per_unit = context.user_data.get('price_per_unit', category_data.get('price_per_unit', 0))
            final_price = context.user_data.get('final_price', quantity * price_per_unit)
            message += f"💰 **السعر لكل وحدة:** {price_per_unit:,} SYP\n\n"
            message += f"📊 **الكمية:** {quantity}\n\n"
            message += f"💰 **السعر الإجمالي:** {final_price:,.2f} SYP\n\n"
        else:
            final_price = context.user_data.get('final_price', category_data.get('price', 0))
            message += f"💰 **السعر:** {final_price:,.2f} SYP\n\n"

        message += f"📝 **{category_data.get('input_label', 'البيانات')}:** {input_data}\n\n"
        message += f"👤 **يرجى إدخال معرف الحساب المراد الدفع إليه:**"

        await update.message.reply_text(message, parse_mode='Markdown')
        return ENTERING_ACCOUNT_ID

    async def show_payment_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query=None) -> int:
        """Show payment confirmation"""
        service_id = context.user_data.get('selected_payment_service')
        category_id = context.user_data.get('selected_payment_category')

        if not service_id or not category_id:
            error_msg = "❌ خطأ: بيانات الطلب غير مكتملة."
            if query:
                await query.edit_message_text(error_msg)
            else:
                await update.message.reply_text(error_msg)
            return MAIN_MENU

        payments = data_manager.get_payments()
        service_data = payments.get(service_id)

        if not service_data:
            error_msg = "❌ خطأ: لم يتم العثور على الخدمة المحددة."
            if query:
                await query.edit_message_text(error_msg)
            else:
                await update.message.reply_text(error_msg)
            return MAIN_MENU

        category_data = service_data['categories'].get(category_id)
        if not category_data:
            error_msg = "❌ خطأ: لم يتم العثور على الفئة المحددة."
            if query:
                await query.edit_message_text(error_msg)
            else:
                await update.message.reply_text(error_msg)
            return MAIN_MENU

        user = update.effective_user
        user_data = data_manager.get_user(user.id)

        pricing_type = category_data.get('pricing_type', 'fixed')

        message = f"🌟 **تأكيد طلب الخدمة**\n\n"
        message += f"📱 القسم: مدفوعات\n\n"
        message += f"🎮 الخدمة: {service_data['name']}\n\n"
        message += f"🏷️ الفئة: {category_data['name']}\n\n"

        if pricing_type == 'quantity':
            quantity = context.user_data.get('quantity', 1)
            price_per_unit = context.user_data.get('price_per_unit', category_data.get('price_per_unit', 0))
            final_price = context.user_data.get('final_price', quantity * price_per_unit)

            message += f"📊 الكمية: {quantity}\n\n"
            message += f"💰 السعر لكل وحدة: {price_per_unit:,} SYP\n\n"
            message += f"💰 السعر الإجمالي: {final_price:,.2f} SYP\n\n"
        else:
            final_price = context.user_data.get('final_price', category_data.get('price', 0))
            message += f"💰 السعر: {final_price:,.2f} SYP\n\n"

        # Add account ID if available
        account_id = context.user_data.get('account_id')
        if account_id:
            message += f"🔑 معرف الحساب: {account_id}\n\n"

        if category_data.get('input_type', 'none') != 'none':
            input_data = context.user_data.get('payment_input_data')
            input_label = category_data.get('input_label', 'البيانات')
            if input_data:
                message += f"📝 {input_label}: {input_data}\n\n"

        # Check user balance
        if user_data['balance'] < final_price:
            error_msg = f"❌ رصيد حسابك غير كافي لشراء هذه الخدمة.\n\n"
            error_msg += f"💰 رصيدك الحالي: {user_data['balance']:,.2f} SYP\n"
            error_msg += f"💸 سعر الخدمة: {final_price:,.2f} SYP\n"
            error_msg += f"📊 تحتاج إلى: {final_price - user_data['balance']:,.2f} SYP إضافية"

            if query:
                await query.edit_message_text(error_msg)
            else:
                await update.message.reply_text(error_msg)
            return MAIN_MENU

        message += f"\n💸 رصيدك الحالي: {user_data['balance']:,.2f} SYP\n"
        message += f"💰 الرصيد بعد الشراء: {user_data['balance'] - final_price:,.2f} SYP\n\n"
        message += "❓ هل تريد تأكيد الطلب؟"

        keyboard = [
            [InlineKeyboardButton("✅ تأكيد الطلب", callback_data="confirm_payment_service_order")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_payment_service_order")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            if query:
                await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error showing payment confirmation: {e}")
            # Fallback without markdown
            if query:
                await query.edit_message_text(message, reply_markup=reply_markup)
            else:
                await update.message.reply_text(message, reply_markup=reply_markup)

        return CONFIRMING_PAYMENT_SERVICE_ORDER

    async def handle_category_delete_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle category selection for deletion"""
        text = update.message.text

        if text == "⬅️ إلغاء":
            return await self.handle_service_selection_for_edit(update, context)

        service_id = context.user_data.get('editing_service_id')
        payments = data_manager.get_payments()
        service_data = payments.get(service_id)

        # Find selected category
        selected_category_id = None
        for cat_id, cat_data in service_data['categories'].items():
            if cat_data['name'] == text:
                selected_category_id = cat_id
                break

        if not selected_category_id:
            await update.message.reply_text("يرجى اختيار فئة من القائمة.")
            return SELECTING_CATEGORY_TO_DELETE

        context.user_data['deleting_category_id'] = selected_category_id
        category_data = service_data['categories'][selected_category_id]

        message = f"⚠️ **تأكيد حذف الفئة**\n\n"
        message += f"الخدمة: **{service_data['name']}**\n"
        message += f"الفئة: **{category_data['name']}**\n"

        pricing_type = category_data.get('pricing_type', 'fixed')
        if pricing_type == 'fixed':
            message += f"السعر: {category_data['price']:,} SYP\n"
        else:
            message += f"السعر: {category_data['price_per_unit']:,} SYP/وحدة\n"

        message += f"\n⚠️ **هذا الإجراء لا يمكن التراجع عنه!**\n"
        message += f"هل أنت متأكد من حذف هذه الفئة؟"

        keyboard = [
            [KeyboardButton("✅ تأكيد الحذف")],
            [KeyboardButton("❌ إلغاء")]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        return CONFIRMING_CATEGORY_DELETE

    async def handle_category_delete_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle category deletion confirmation"""
        text = update.message.text

        if text == "❌ إلغاء":
            await update.message.reply_text("تم إلغاء عملية الحذف.")
            return await self.handle_service_selection_for_edit(update, context)

        elif text == "✅ تأكيد الحذف":
            service_id = context.user_data.get('editing_service_id')
            category_id = context.user_data.get('deleting_category_id')

            # Delete the category
            settings = data_manager._load_json(data_manager.settings_file)
            if service_id in settings['payment_services'] and category_id in settings['payment_services'][service_id]['categories']:
                category_name = settings['payment_services'][service_id]['categories'][category_id]['name']
                del settings['payment_services'][service_id]['categories'][category_id]
                data_manager._save_json(data_manager.settings_file, settings)

                await update.message.reply_text(f"✅ تم حذف الفئة '{category_name}' بنجاح!")
            else:
                await update.message.reply_text("❌ فشل في حذف الفئة.")

            context.user_data.pop('deleting_category_id', None)
            return await self.handle_service_selection_for_edit(update, context)

        else:
            await update.message.reply_text("يرجى اختيار تأكيد الحذف أو الإلغاء.")
            return CONFIRMING_CATEGORY_DELETE

    async def handle_category_edit_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle category selection for editing"""
        text = update.message.text

        if text == "⬅️ إلغاء":
            return await self.handle_service_selection_for_edit(update, context)

        service_id = context.user_data.get('editing_service_id')
        payments = data_manager.get_payments()
        service_data = payments.get(service_id)

        # Extract category name from text (remove price info)
        category_name = text.split(" - ")[0] if " - " in text else text

        # Find selected category
        selected_category_id = None
        for cat_id, cat_data in service_data['categories'].items():
            if cat_data['name'] == category_name:
                selected_category_id = cat_id
                break

        if not selected_category_id:
            await update.message.reply_text("يرجى اختيار فئة من القائمة.")
            return SELECTING_CATEGORY_TO_EDIT

        context.user_data['editing_category_id'] = selected_category_id
        category_data = service_data['categories'][selected_category_id]

        message = f"✏️ **تعديل الفئة**\n\n"
        message += f"الخدمة: **{service_data['name']}**\n"
        message += f"الفئة: **{category_data['name']}**\n"

        pricing_type = category_data.get('pricing_type', 'fixed')
        if pricing_type == 'fixed':
            message += f"السعر الحالي: {category_data['price']:,} SYP\n\n"
            message += f"أدخل السعر الجديد:"
        else:
            message += f"السعر الحالي: {category_data['price_per_unit']:,} SYP/وحدة\n\n"
            message += f"أدخل السعر الجديد لكل وحدة:"

        await update.message.reply_text(message, parse_mode='Markdown')
        return EDITING_CATEGORY_PRICE

    async def handle_category_price_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle category price editing"""
        try:
            new_price = int(update.message.text.strip())
            if new_price <= 0:
                raise ValueError

            service_id = context.user_data.get('editing_service_id')
            category_id = context.user_data.get('editing_category_id')

            settings = data_manager._load_json(data_manager.settings_file)
            service_data = settings['payment_services'][service_id]
            category_data = service_data['categories'][category_id]

            pricing_type = category_data.get('pricing_type', 'fixed')
            old_price = category_data.get('price') if pricing_type == 'fixed' else category_data.get('price_per_unit')

            message = f"✏️ **تأكيد تعديل السعر**\n\n"
            message += f"الخدمة: **{service_data['name']}**\n"
            message += f"الفئة: **{category_data['name']}**\n"

            if pricing_type == 'fixed':
                message += f"السعر القديم: {old_price:,} SYP\n"
                message += f"السعر الجديد: {new_price:,} SYP\n\n"
            else:
                message += f"السعر القديم: {old_price:,} SYP/وحدة\n"
                message += f"السعر الجديد: {new_price:,} SYP/وحدة\n\n"

            message += f"هل تريد تأكيد التعديل؟"

            context.user_data['new_category_price'] = new_price

            keyboard = [
                [InlineKeyboardButton("✅ تأكيد التعديل", callback_data="confirm_category_edit")],
                [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_category_edit")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            return CONFIRMING_CATEGORY_EDIT

        except ValueError:
            await update.message.reply_text("يرجى إدخال سعر صحيح (رقم موجب):")
            return EDITING_CATEGORY_PRICE

    async def handle_category_edit_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle category edit confirmation"""
        query = update.callback_query
        await query.answer()

        if query.data == "cancel_category_edit":
            await query.edit_message_text("تم إلغاء التعديل.")
            return await self.handle_service_selection_for_edit(update, context)

        elif query.data == "confirm_category_edit":
            service_id = context.user_data.get('editing_service_id')
            category_id = context.user_data.get('editing_category_id')
            new_price = context.user_data.get('new_category_price')

            # Update the category price
            settings = data_manager._load_json(data_manager.settings_file)
            category_data = settings['payment_services'][service_id]['categories'][category_id]

            pricing_type = category_data.get('pricing_type', 'fixed')
            if pricing_type == 'fixed':
                settings['payment_services'][service_id]['categories'][category_id]['price'] = new_price
            else:
                settings['payment_services'][service_id]['categories'][category_id]['price_per_unit'] = new_price

            data_manager._save_json(data_manager.settings_file, settings)

            price_type_text = "السعر" if pricing_type == 'fixed' else "السعر لكل وحدة"
            await query.edit_message_text(
                f"✅ تم تعديل {price_type_text} للفئة '{category_data['name']}' بنجاح!\n"
                f"💰 {price_type_text} الجديد: {new_price:,} SYP"
            )

            context.user_data.pop('editing_category_id', None)
            context.user_data.pop('new_category_price', None)
            return ADDING_SERVICE_CATEGORIES

    async def show_user_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show user management interface"""
        message = "👥 **إدارة المستخدمين**\n\nاختر العملية:"

        keyboard = [
            [KeyboardButton("البحث عن مستخدم 🔍")],
            [KeyboardButton("حظر مستخدم 🚫"), KeyboardButton("فك حظر مستخدم ✅")],
            [KeyboardButton("تجميد حساب ❄️"), KeyboardButton("فك تجميد حساب 🌡️")],
            [KeyboardButton("حذف حساب مستخدم 🗑️")],
            [KeyboardButton("تعديل رصيد (صامت) 💰")],
            [KeyboardButton("إرسال رسالة خاصة 📩")],
            [KeyboardButton("⬅️ العودة للوحة التحكم")]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return USER_MANAGEMENT

    async def handle_show_my_statistics_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle show my statistics callback button"""
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id

        try:
            # Get all orders for this user
            orders = data_manager._load_json(data_manager.orders_file)
            user_orders = [order for order in orders.values() if order.get('user_id') == user_id]

            # Filter completed orders only
            completed_orders = [order for order in user_orders if order.get('status') in ['مكتمل وتم الشحن بنجاح', 'تم الموافقة', 'تم التنفيذ']]

            # Initialize counters
            app_orders = 0
            app_total = 0
            game_orders = 0
            game_total = 0
            payment_orders = 0
            payment_total = 0

            # Count orders by type
            for order in completed_orders:
                order_price = order.get('price', 0)
                service_type = order.get('service_type', '')

                if service_type == 'app':
                    app_orders += 1
                    app_total += order_price
                elif service_type == 'game':
                    game_orders += 1
                    game_total += order_price
                elif service_type == 'payment_service':
                    payment_orders += 1
                    payment_total += order_price

            # Calculate totals
            total_orders = app_orders + game_orders + payment_orders
            total_amount = app_total + game_total + payment_total

            bot_name = data_manager.get_bot_name(english=False)
            message = f"📊 بياناتي في {bot_name}\n\n"

            message += f"📱 طلبات التطبيقات: {app_orders} طلب بقيمة {app_total:,.2f} SYP\n\n"

            message += f"🎮 طلبات الألعاب: {game_orders} طلب بقيمة {game_total:,.2f} SYP\n\n"

            message += f"💳 طلبات المدفوعات: {payment_orders} طلب بقيمة {payment_total:,.2f} SYP\n\n"

            message += f"──────────────────────────\n"
            message += f"📦 إجمالي الطلبات: {total_orders}\n"
            message += f"💰 مجموع الإنفاق: {total_amount:,.2f} SYP\n\n"

            message += f"══════════════════════════"

            # Create back button
            keyboard = [[InlineKeyboardButton("⬅️ العودة", callback_data="back_to_main")]]

            # Delete the old message first
            try:
                await query.delete_message()
            except Exception:
                pass

            # Send message with back button
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(message, reply_markup=reply_markup)

            return MAIN_MENU

        except Exception as e:
            logger.error(f"Error showing user statistics: {e}")
            await query.message.reply_text(
                "❌ حدث خطأ في عرض البيانات. يرجى المحاولة لاحقاً."
            )
            return MAIN_MENU

    async def show_user_statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show user personal statistics"""
        user_id = update.effective_user.id

        try:
            # Get all orders for this user
            orders = data_manager._load_json(data_manager.orders_file)
            user_orders = [order for order in orders.values() if order.get('user_id') == user_id]

            # Filter completed orders only
            completed_orders = [order for order in user_orders if order.get('status') in ['مكتمل وتم الشحن بنجاح', 'تم الموافقة', 'تم التنفيذ']]

            # Initialize counters
            app_orders = 0
            app_total = 0
            game_orders = 0
            game_total = 0
            payment_orders = 0
            payment_total = 0

            # Count orders by type
            for order in completed_orders:
                order_price = order.get('price', 0)
                service_type = order.get('service_type', '')

                if service_type == 'app':
                    app_orders += 1
                    app_total += order_price
                elif service_type == 'game':
                    game_orders += 1
                    game_total += order_price
                elif service_type == 'payment_service':
                    payment_orders += 1
                    payment_total += order_price

            # Calculate totals
            total_orders = app_orders + game_orders + payment_orders
            total_amount = app_total + game_total + payment_total

            bot_name = data_manager.get_bot_name(english=False)
            message = f"شكراً لإستخدامك {bot_name}\n\n"

            message += f"مجموع طلبات التطبيق المكتملة {app_orders} بـ قيمة {app_total:,.2f} SYP\n\n"

            message += f"مجموع طلبات الالعاب المكتملة {game_orders} بـ قيمة {game_total:,.2f} SYP\n\n"

            message += f"مجموع طلبات المدفوعات المكتملة {payment_orders} بـ قيمة {payment_total:,.2f} SYP\n\n"

            message += f"إجمالي الطلبات: {total_orders}\n"
            message += f"بمجموع إنفاق: {total_amount:,.2f} SYP"

            # Send without parse_mode to avoid formatting errors
            await update.message.reply_text(message)

            return MAIN_MENU

        except Exception as e:
            logger.error(f"Error showing user statistics: {e}")
            await update.message.reply_text(
                "❌ حدث خطأ في عرض البيانات. يرجى المحاولة لاحقاً."
            )
            return MAIN_MENU

    async def show_statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show comprehensive statistics"""
        try:
            stats = data_manager.get_user_statistics()

            message = f"📊 إحصائيات شاملة للبوت\n\n"

            # User statistics
            message += f"👥 إحصائيات المستخدمين:\n"
            message += f"• العدد الإجمالي: {stats['total_users']:,} مستخدم\n"
            message += f"• المحظورون: {stats['banned_users']:,} مستخدم\n"
            message += f"• المجمدون: {stats['frozen_users']:,} مستخدم\n"
            message += f"• مجموع أرصدة المستخدمين: {stats['total_user_balance']:,.2f} SYP\n"
            message += f"• مجموع إنفاق المستخدمين: {stats['total_user_spending']:,.2f} SYP\n\n"

            # Financial overview
            message += f"💰 الإحصائيات المالية:\n"
            message += f"• إجمالي الإيرادات: {stats['total_revenue']:,.2f} SYP\n"
            message += f"• الإيرادات المعلقة: {stats['pending_revenue']:,.2f} SYP\n"
            message += f"• متوسط قيمة الطلب: {stats['avg_order_value']:,.2f} SYP\n"
            message += f"• الأرصدة المتبقية: {stats['total_balance']:,.2f} SYP\n\n"

            # Orders statistics
            message += f"📦 إحصائيات الطلبات:\n"
            message += f"• إجمالي الطلبات: {stats['total_orders']:,}\n"
            message += f"• المكتملة: {stats['completed_orders_count']:,} طلب\n"
            message += f"• قيد المعالجة: {stats['pending_orders_count']:,} طلب\n"
            message += f"• المرفوضة: {stats['rejected_orders_count']:,} طلب\n\n"

            # Revenue by service type
            message += f"📊 الإيرادات حسب نوع الخدمة:\n"
            message += f"• التطبيقات: {stats['app_revenue']:,.2f} SYP ({stats['app_orders_count']} طلب)\n"
            message += f"• الألعاب: {stats['game_revenue']:,.2f} SYP ({stats['game_orders_count']} طلب)\n"
            message += f"• المدفوعات: {stats['payment_revenue']:,.2f} SYP ({stats['payment_orders_count']} طلب)\n\n"

            # Top spenders
            if stats['top_spenders']:
                message += f"💸 أكثر 3 مستخدمين إنفاقاً:\n"
                for i, user in enumerate(stats['top_spenders'], 1):
                    emoji = ["🥇", "🥈", "🥉"][i-1]
                    username = user.get('username', f"User_{user['user_id']}")
                    message += f"{emoji} {username}: {user['total_spent']:,} SYP ({user['order_count']} طلب)\n"
                message += "\n"

            # Top balance holders
            if stats['top_3_users']:
                message += f"💰 أكثر 3 مستخدمين رصيداً:\n"
                for i, user in enumerate(stats['top_3_users'], 1):
                    emoji = ["🥇", "🥈", "🥉"][i-1]
                    username = user.get('username', f"User_{user['user_id']}")
                    message += f"{emoji} {username}: {user['balance']:,.2f} SYP\n"
                message += "\n"

            # Agent statistics
            if stats['total_agents'] > 0:
                message += f"🤝 إحصائيات الوكلاء:\n"
                message += f"• إجمالي الوكلاء: {stats['total_agents']}\n"
                message += f"• الوكلاء النشطون: {stats['active_agents']}\n"
                message += f"• إجمالي أرباح الوكلاء: {stats['total_agent_earnings']:,.2f} SYP\n\n"

            message += f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            keyboard = [
                [KeyboardButton("تحديث الإحصائيات 🔄")],
                [KeyboardButton("إحصائيات مفصلة 📈")],
                [KeyboardButton("⬅️ العودة للوحة التحكم")]
            ]

            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(message, reply_markup=reply_markup)

            return VIEWING_STATISTICS
        except Exception as e:
            logger.error(f"Error showing statistics: {e}")
            await update.message.reply_text(
                "❌ حدث خطأ في عرض الإحصائيات. يرجى المحاولة لاحقاً."
            )
            return await self.show_admin_panel(update, context)

    async def handle_user_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle user management menu selection"""
        text = update.message.text

        if text == "البحث عن مستخدم 🔍":
            await update.message.reply_text(
                "🔍 أدخل معرف المستخدم أو جزء من اسم المستخدم للبحث:\n\n"
                "مثال: 123456789"
            )
            return ENTERING_USER_ID_FOR_ACTION

        elif text in ["حظر مستخدم 🚫", "فك حظر مستخدم ✅", "تجميد حساب ❄️", "فك تجميد حساب 🌡️", "حذف حساب مستخدم 🗑️"]:
            context.user_data['selected_action'] = text
            await update.message.reply_text("أدخل معرف المستخدم:")
            return ENTERING_USER_ID_FOR_ACTION

        elif text == "تعديل رصيد (صامت) 💰":
            context.user_data['selected_action'] = text
            await update.message.reply_text("أدخل معرف المستخدم:")
            return ENTERING_USER_ID_FOR_ACTION

        elif text == "إرسال رسالة خاصة 📩":
            await update.message.reply_text("أدخل معرف المستخدم المراد إرسال الرسالة إليه:")
            return ENTERING_PRIVATE_MESSAGE_USER_ID

        elif text == "⬅️ العودة للوحة التحكم":
            return await self.show_admin_panel(update, context)

        else:
            await update.message.reply_text("يرجى اختيار خيار صحيح من القائمة.")
            return USER_MANAGEMENT

    async def handle_statistics_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle statistics menu actions"""
        text = update.message.text

        if text == "تحديث الإحصائيات 🔄":
            return await self.show_statistics(update, context)

        elif text == "إحصائيات مفصلة 📈":
            return await self.show_detailed_statistics(update, context)

        elif text == "⬅️ العودة للإحصائيات العامة":
            return await self.show_statistics(update, context)

        elif text == "⬅️ العودة للوحة التحكم":
            return await self.show_admin_panel(update, context)

        else:
            await update.message.reply_text("يرجى اختيار خيار صحيح من القائمة.")
            return VIEWING_STATISTICS

    async def show_detailed_statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show detailed financial statistics"""
        try:
            stats = data_manager.get_user_statistics()
            orders = data_manager._load_json(data_manager.orders_file)

            message = f"📈 إحصائيات مالية مفصلة\n\n"

            # Revenue breakdown
            message += f"💰 تفصيل الإيرادات:\n"
            message += f"━━━━━━━━━━━━━━━━━━━━━━\n"
            message += f"إجمالي المبيعات: {stats['total_revenue']:,.2f} SYP\n"
            message += f"المبيعات المعلقة: {stats['pending_revenue']:,.2f} SYP\n"
            message += f"متوسط الطلب: {stats['avg_order_value']:,.2f} SYP\n\n"

            # Service breakdown
            total_service_revenue = stats['app_revenue'] + stats['game_revenue'] + stats['payment_revenue']
            if total_service_revenue > 0:
                app_percentage = (stats['app_revenue'] / total_service_revenue) * 100
                game_percentage = (stats['game_revenue'] / total_service_revenue) * 100
                payment_percentage = (stats['payment_revenue'] / total_service_revenue) * 100

                message += f"📊 توزيع الإيرادات:\n"
                message += f"━━━━━━━━━━━━━━━━━━━━━━\n"
                message += f"التطبيقات: {stats['app_revenue']:,.2f} SYP ({app_percentage:.1f}%)\n"
                message += f"الألعاب: {stats['game_revenue']:,.2f} SYP ({game_percentage:.1f}%)\n"
                message += f"المدفوعات: {stats['payment_revenue']:,.2f} SYP ({payment_percentage:.1f}%)\n\n"

            # Monthly analysis (last 30 days)
            from datetime import datetime, timedelta
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_orders = []

            for order in orders.values():
                try:
                    order_date = datetime.fromisoformat(order.get('timestamp', ''))
                    if order_date >= thirty_days_ago and order.get('status') in ['مكتمل وتم الشحن بنجاح', 'تم الموافقة', 'تم التنفيذ']:
                        recent_orders.append(order)
                except:
                    continue

            if recent_orders:
                monthly_revenue = sum(order.get('price', 0) for order in recent_orders)
                daily_average = monthly_revenue / 30
                message += f"📅 آخر 30 يوماً:\n"
                message += f"━━━━━━━━━━━━━━━━━━━━━━\n"
                message += f"الإيرادات: {monthly_revenue:,.2f} SYP\n"
                message += f"الطلبات: {len(recent_orders):,} طلب\n"
                message += f"متوسط يومي: {daily_average:,.2f} SYP\n\n"

            # Agent economics
            if stats['total_agents'] > 0:
                agent_percentage = (stats['total_agent_earnings'] / stats['total_revenue']) * 100 if stats['total_revenue'] > 0 else 0
                message += f"🤝 اقتصاديات الوكلاء:\n"
                message += f"━━━━━━━━━━━━━━━━━━━━━━\n"
                message += f"إجمالي الوكلاء: {stats['total_agents']}\n"
                message += f"الوكلاء النشطون: {stats['active_agents']}\n"
                message += f"أرباح الوكلاء: {stats['total_agent_earnings']:,.2f} SYP\n"
                message += f"نسبة أرباح الوكلاء: {agent_percentage:.1f}%\n\n"

            # User economics
            if stats['total_users'] > 0:
                avg_balance_per_user = stats['total_balance'] / stats['total_users']
                avg_spending_per_user = stats['total_user_spending'] / stats['total_users']
                spending_users = len([user for user in stats['top_spenders']])
                spending_rate = (spending_users / stats['total_users']) * 100 if stats['total_users'] > 0 else 0

                message += f"👥 اقتصاديات المستخدمين:\n"
                message += f"━━━━━━━━━━━━━━━━━━━━━━\n"
                message += f"مجموع الأرصدة: {stats['total_user_balance']:,.2f} SYP\n"
                message += f"مجموع الإنفاق: {stats['total_user_spending']:,.2f} SYP\n"
                message += f"متوسط الرصيد: {avg_balance_per_user:,.2f} SYP\n"
                message += f"متوسط الإنفاق: {avg_spending_per_user:,.2f} SYP\n"
                message += f"المستخدمون المنفقون: {spending_users}\n"
                message += f"معدل الإنفاق: {spending_rate:.1f}%\n\n"

            # Success rate
            if stats['total_orders'] > 0:
                success_rate = (stats['completed_orders_count'] / stats['total_orders']) * 100
                rejection_rate = (stats['rejected_orders_count'] / stats['total_orders']) * 100
                message += f"📊 معدلات النجاح:\n"
                message += f"━━━━━━━━━━━━━━━━━━━━━━\n"
                message += f"معدل النجاح: {success_rate:.1f}%\n"
                message += f"معدل الرفض: {rejection_rate:.1f}%\n"
                message += f"معدل الانتظار: {(stats['pending_orders_count']/stats['total_orders']*100):.1f}%\n\n"

            message += f"📅 تم التحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            keyboard = [
                [KeyboardButton("⬅️ العودة للإحصائيات العامة")]
            ]

            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(message, reply_markup=reply_markup)

            return VIEWING_STATISTICS
        except Exception as e:
            logger.error(f"Error showing detailed statistics: {e}")
            await update.message.reply_text(
                "❌ حدث خطأ في عرض الإحصائيات المفصلة. يرجى المحاولة لاحقاً."
            )
            return await self.show_statistics(update, context)

    async def handle_user_id_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle user ID input for various actions"""
        user_input = update.message.text.strip()
        action = context.user_data.get('selected_action')

        # Try to parse as user ID first
        try:
            user_id = int(user_input)
            context.user_data['target_user_id'] = user_id

            # Get user details
            user_details = data_manager.get_user_details(user_id)

            if not user_details:
                await update.message.reply_text("❌ المستخدم غير موجود في قاعدة البيانات.")
                return USER_MANAGEMENT

            # For search, always show details directly
            if not action or action == "البحث عن مستخدم 🔍":
                return await self.show_user_details(update, context, user_details)
            elif action == "تعديل رصيد (صامت) 💰":
                await update.message.reply_text(
                    f"الرصيد الحالي للمستخدم {user_id}: {user_details['balance']:,.2f} SYP\n\n"
                    "أدخل الرصيد الجديد:"
                )
                return ENTERING_BALANCE_AMOUNT
            elif action == "تجميد حساب ❄️":
                if user_details.get('is_frozen'):
                    await update.message.reply_text("❄️ المستخدم مجمد بالفعل.")
                    return USER_MANAGEMENT
                await update.message.reply_text(
                    "أدخل مدة التجميد:\n\n"
                    "1 = دقيقة واحدة\n"
                    "60 = ساعة واحدة\n"
                    "1440 = يوم واحد\n"
                    "10080 = أسبوع واحد\n\n"
                    "أدخل المدة بالدقائق:"
                )
                return ENTERING_FREEZE_DURATION
            else:
                return await self.show_user_action_confirmation(update, context, user_details)

        except ValueError:
            # Search by username
            search_results = data_manager.search_user(user_input)

            if not search_results:
                await update.message.reply_text("❌ لم يتم العثور على أي مستخدم.")
                return USER_MANAGEMENT

            if len(search_results) == 1:
                context.user_data['target_user_id'] = search_results[0]['user_id']
                # For search, always show details directly
                if not action or action == "البحث عن مستخدم 🔍":
                    return await self.show_user_details(update, context, search_results[0])
                else:
                    return await self.show_user_action_confirmation(update, context, search_results[0])
            else:
                # Multiple results - show list
                message = f"🔍 تم العثور على {len(search_results)} نتيجة:\n\n"
                for i, user in enumerate(search_results, 1):
                    username = user.get('username', 'غير محدد')
                    message += f"{i}. ID: {user['user_id']} | الرصيد: {user['balance']:,.2f} SYP\n"

                message += "\nأدخل معرف المستخدم المحدد:"
                await update.message.reply_text(message)
                return ENTERING_USER_ID_FOR_ACTION

    async def show_user_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_details: Dict) -> int:
        """Show detailed user information"""
        try:
            user_id = user_details['user_id']

            message = f"👤 تفاصيل المستخدم الكاملة\n\n"
            message += f"🆔 معرف المستخدم: {user_id}\n"

            # Get additional user info
            user_data = data_manager.get_user(user_id)

            # Username if available
            username = user_details.get('username', 'غير محدد')
            message += f"👨‍💻 اسم المستخدم: {username}\n"

            # Balance
            message += f"💰 الرصيد: {user_details['balance']:,.2f} SYP\n"

            # Account creation date
            created_date = datetime.fromisoformat(user_details['created_at'])
            message += f"📅 تاريخ إنشاء الحساب: {created_date.strftime('%Y-%m-%d %H:%M:%S')}\n"

            # Account age
            account_age = datetime.now() - created_date
            if account_age.days > 0:
                message += f"⏰ عمر الحساب: {account_age.days} يوم\n"
            else:
                hours = account_age.seconds // 3600
                message += f"⏰ عمر الحساب: {hours} ساعة\n"

            # Status section
            message += f"\n📊 حالة الحساب:\n"

            # Check if banned
            if user_details.get('is_banned', False):
                banned_date = datetime.fromisoformat(user_details['banned_at']).strftime('%Y-%m-%d %H:%M:%S')
                message += f"🚫 محظور منذ: {banned_date}\n"

            # Check if frozen
            if user_details.get('is_frozen', False):
                message += f"❄️ مجمد حتى: {user_details['frozen_until_formatted']}\n"

            # If not banned or frozen
            if not user_details.get('is_banned', False) and not user_details.get('is_frozen', False):
                message += f"✅ نشط وغير محظور\n"

            # Orders information
            orders_count = len(user_details.get('orders', []))
            message += f"\n📦 إحصائيات الطلبات:\n"
            message += f"• العدد الإجمالي: {orders_count} طلب\n"

            # Get orders from orders file to show more details
            try:
                orders = data_manager._load_json(data_manager.orders_file)
                user_orders = [order for order in orders.values() if order.get('user_id') == user_id]

                if user_orders:
                    # Calculate total spent
                    total_spent = sum(order.get('price', 0) for order in user_orders)
                    message += f"• إجمالي المبلغ المنفق: {total_spent:,} SYP\n"

                    # Order statuses
                    completed_orders = len([o for o in user_orders if o.get('status') in ['تم الموافقة', 'تم التنفيذ']])
                    pending_orders = len([o for o in user_orders if o.get('status') == 'قيد المعالجة'])
                    rejected_orders = len([o for o in user_orders if o.get('status') == 'مرفوض'])

                    message += f"• الطلبات المكتملة: {completed_orders}\n"
                    if pending_orders > 0:
                        message += f"• الطلبات المعلقة: {pending_orders}\n"
                    if rejected_orders > 0:
                        message += f"• الطلبات المرفوضة: {rejected_orders}\n"

                    # Last order info
                    latest_order = max(user_orders, key=lambda x: x.get('timestamp', ''))
                    if latest_order:
                        message += f"• آخر طلب: {latest_order.get('timestamp', 'غير محدد')}\n"
                else:
                    message += f"• لا توجد طلبات مسجلة\n"

            except Exception as e:
                logger.error(f"Error getting user orders: {e}")
                message += f"• خطأ في جلب تفاصيل الطلبات\n"

            # Additional user data
            message += f"\n📋 معلومات إضافية:\n"

            # Check if user has any additional data
            if 'phone' in user_data:
                message += f"📱 الهاتف: {user_data['phone']}\n"
            if 'email' in user_data:
                message += f"📧 البريد: {user_data['email']}\n"

            # Last activity (if available)
            if 'last_activity' in user_data:
                last_activity = datetime.fromisoformat(user_data['last_activity']).strftime('%Y-%m-%d %H:%M:%S')
                message += f"🕐 آخر نشاط: {last_activity}\n"

            # System info
            message += f"\n🔧 معلومات النظام:\n"
            message += f"📊 تم عرض التفاصيل في: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

            # Send message without any buttons
            await update.message.reply_text(message)

            return USER_MANAGEMENT
        except Exception as e:
            logger.error(f"Error showing user details: {e}")
            await update.message.reply_text(
                f"❌ حدث خطأ في عرض تفاصيل المستخدم {user_details.get('user_id', 'غير معروف')}."
            )
            return await self.show_user_management(update, context)

    async def show_user_action_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_details: Dict) -> int:
        """Show confirmation for user actions"""
        action = context.user_data.get('selected_action')
        user_id = user_details['user_id']

        action_map = {
            "حظر مستخدم 🚫": ("حظر", "ban"),
            "فك حظر مستخدم ✅": ("فك حظر", "unban"),
            "فك تجميد حساب 🌡️": ("فك تجميد", "unfreeze"),
            "حذف حساب مستخدم 🗑️": ("حذف", "delete")
        }

        action_text, action_code = action_map.get(action, ("عملية", "action"))

        message = f"⚠️ **تأكيد {action_text} المستخدم**\n\n"
        message += f"🆔 معرف المستخدم: `{user_id}`\n"
        message += f"💰 الرصيد: {user_details['balance']:,.2f} SYP\n\n"

        if action_code == "delete":
            message += f"⚠️ **تحذير**: سيتم حذف المستخدم نهائياً مع جميع بياناته!\n"

        message += f"هل أنت متأكد من {action_text} هذا المستخدم؟"

        keyboard = [
            [InlineKeyboardButton(f"✅ تأكيد {action_text}", callback_data=f"confirm_action_{action_code}_{user_id}")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_user_action")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return CONFIRMING_USER_ACTION

    async def handle_freeze_duration_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle freeze duration input"""
        try:
            duration_minutes = int(update.message.text.strip())

            if duration_minutes < 1:
                raise ValueError("Duration must be positive")

            if duration_minutes > 10080:  # Max 1 week
                await update.message.reply_text("❌ الحد الأقصى للتجميد هو أسبوع واحد (10080 دقيقة).")
                return ENTERING_FREEZE_DURATION

            user_id = context.user_data.get('target_user_id')

            # Convert duration to readable format
            if duration_minutes < 60:
                duration_text = f"{duration_minutes} دقيقة"
            elif duration_minutes < 1440:
                hours = duration_minutes // 60
                remaining_minutes = duration_minutes % 60
                duration_text = f"{hours} ساعة"
                if remaining_minutes > 0:
                    duration_text += f" و {remaining_minutes} دقيقة"
            else:
                days = duration_minutes // 1440
                remaining_hours = (duration_minutes % 1440) // 60
                duration_text = f"{days} يوم"
                if remaining_hours > 0:
                    duration_text += f" و {remaining_hours} ساعة"

            context.user_data['freeze_duration'] = duration_minutes

            message = f"⚠️ **تأكيد تجميد المستخدم**\n\n"
            message += f"🆔 معرف المستخدم: `{user_id}`\n"
            message += f"❄️ مدة التجميد: {duration_text}\n"
            message += f"🕐 سينتهي التجميد في: {(datetime.now() + timedelta(minutes=duration_minutes)).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            message += f"هل أنت متأكد من تجميد هذا المستخدم؟"

            keyboard = [
                [InlineKeyboardButton("✅ تأكيد التجميد", callback_data=f"confirm_freeze_{user_id}")],
                [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_user_action")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

            return CONFIRMING_USER_ACTION

        except ValueError:
            await update.message.reply_text("❌ يرجى إدخال رقم صحيح للمدة بالدقائق.")
            return ENTERING_FREEZE_DURATION

    async def handle_balance_amount_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle balance amount input for silent update"""
        try:
            new_balance = int(update.message.text.strip())

            if new_balance < 0:
                await update.message.reply_text("❌ الرصيد لا يمكن أن يكون سالباً.")
                return ENTERING_BALANCE_AMOUNT

            user_id = context.user_data.get('target_user_id')
            old_balance = data_manager.get_user(user_id)['balance']

            # Update balance silently
            data_manager.update_user_balance_silent(user_id, new_balance)

            message = f"✅ **تم تعديل الرصيد بنجاح**\n\n"
            message += f"🆔 معرف المستخدم: `{user_id}`\n"
            message += f"💰 الرصيد السابق: {old_balance:,} SYP\n"
            message += f"💰 الرصيد الجديد: {new_balance:,} SYP\n"
            message += f"📊 الفرق: {new_balance - old_balance:+,} SYP\n\n"
            message += f"ℹ️ تم التعديل بصمت بدون إشعار المستخدم"

            await update.message.reply_text(message, parse_mode='Markdown')

            context.user_data.clear()
            return await self.show_user_management(update, context)

        except ValueError:
            await update.message.reply_text("❌ يرجى إدخال رقم صحيح للرصيد.")
            return ENTERING_BALANCE_AMOUNT

    async def handle_private_message_user_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle user ID input for private message"""
        try:
            user_id = int(update.message.text.strip())

            # Check if user exists
            user_details = data_manager.get_user_details(user_id)
            if not user_details:
                await update.message.reply_text("❌ المستخدم غير موجود في قاعدة البيانات.")
                return USER_MANAGEMENT

            context.user_data['private_message_user_id'] = user_id

            await update.message.reply_text(
                f"📩 أدخل الرسالة التي تريد إرسالها للمستخدم `{user_id}`:\n\n"
                "يمكنك استخدام تنسيق Markdown للنص.",
                parse_mode='Markdown'
            )
            return ENTERING_PRIVATE_MESSAGE_TEXT

        except ValueError:
            await update.message.reply_text("❌ يرجى إدخال معرف مستخدم صحيح.")
            return ENTERING_PRIVATE_MESSAGE_USER_ID

    async def handle_private_message_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle private message text input"""
        message_text = update.message.text
        user_id = context.user_data.get('private_message_user_id')

        if not message_text.strip():
            await update.message.reply_text("❌ يرجى إدخال نص الرسالة.")
            return ENTERING_PRIVATE_MESSAGE_TEXT

        context.user_data['private_message_text'] = message_text

        # Show preview
        preview_message = f"📩 **معاينة الرسالة الخاصة**\n\n"
        preview_message += f"🎯 إلى المستخدم: `{user_id}`\n\n"
        preview_message += f"💬 **الرسالة:**\n{message_text}\n\n"
        preview_message += f"هل تريد إرسال هذه الرسالة؟"

        keyboard = [
            [InlineKeyboardButton("✅ إرسال الرسالة", callback_data=f"send_private_message_{user_id}")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_private_message")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(preview_message, reply_markup=reply_markup, parse_mode='Markdown')

        return CONFIRMING_PRIVATE_MESSAGE

    async def show_agents_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show agents management interface"""
        agents = data_manager.get_agents()

        message = "🤝 **إدارة الوكلاء**\n\n"

        if agents:
            message += f"عدد الوكلاء: {len(agents)}\n\n"
            total_earnings = sum(agent.get('total_earnings', 0) for agent in agents.values())
            total_orders = sum(agent.get('total_orders', 0) for agent in agents.values())
            message += f"إجمالي الأرباح: {total_earnings:,.2f} SYP\n"
            message += f"إجمالي العمليات: {total_orders}\n\n"
        else:
            message += "لا يوجد وكلاء مسجلون حالياً\n\n"

        message += "اختر العملية:"

        keyboard = [
            [KeyboardButton("إضافة وكيل ➕")],
            [KeyboardButton("تعديل أرباح وكيل 💰"), KeyboardButton("حذف وكيل 🗑️")],
            [KeyboardButton("تعديل بيانات وكيل ✏️"), KeyboardButton("إحصائيات وكيل 📊")],
            [KeyboardButton("إدارة رصيد وكيل 💳")],
            [KeyboardButton("تعيين رسوم السحب ⚙️")],
            [KeyboardButton("⬅️ العودة للوحة التحكم")]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return MANAGING_AGENTS

    async def handle_agents_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle agents management menu selection"""
        text = update.message.text

        if text == "إضافة وكيل ➕":
            await update.message.reply_text("أدخل اسم الوكيل:")
            return ENTERING_AGENT_NAME

        elif text == "تعديل أرباح وكيل 💰":
            return await self.show_agents_list_for_action(update, context, "edit_commission")

        elif text == "حذف وكيل 🗑️":
            return await self.show_agents_list_for_action(update, context, "delete")

        elif text == "تعديل بيانات وكيل ✏️":
            return await self.show_agents_list_for_action(update, context, "edit_data")

        elif text == "إحصائيات وكيل 📊":
            return await self.show_agents_list_for_action(update, context, "statistics")

        elif text == "تعيين رسوم السحب ⚙️":
            current_fees = data_manager.get_withdrawal_fees()
            await update.message.reply_text(
                f"رسوم السحب الحالية: {current_fees}%\n\n"
                "أدخل نسبة رسوم السحب الجديدة (بالنسبة المئوية):"
            )
            return SETTING_WITHDRAWAL_FEES

        elif text == "إدارة رصيد وكيل 💳":
            return await self.show_agents_balance_management(update, context)

        elif text == "⬅️ العودة للوحة التحكم":
            return await self.show_admin_panel(update, context)

        else:
            await update.message.reply_text("يرجى اختيار خيار صحيح من القائمة.")
            return MANAGING_AGENTS

    async def show_agents_list_for_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> int:
        """Show list of agents for specific action"""
        agents = data_manager.get_agents()

        if not agents:
            await update.message.reply_text("لا يوجد وكلاء مسجلون.")
            return await self.show_agents_management(update, context)

        context.user_data['agent_action'] = action

        action_names = {
            "edit_commission": "تعديل نسبة الربح",
            "delete": "حذف الوكيل",
            "edit_data": "تعديل البيانات",
            "statistics": "عرض الإحصائيات"
        }

        message = f"📋 {action_names.get(action, 'اختيار')} - اختر الوكيل:\n\n"

        keyboard = []
        for agent_id, agent_data in agents.items():
            button_text = f"{agent_data['name']} ({agent_data['commission_rate']}%)"
            keyboard.append([KeyboardButton(button_text)])

        keyboard.append([KeyboardButton("⬅️ العودة")])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(message, reply_markup=reply_markup)
        return SELECTING_AGENT_TO_EDIT

    async def handle_agent_name_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle agent name entry"""
        agent_name = update.message.text.strip()

        if not agent_name:
            await update.message.reply_text("يرجى إدخال اسم صحيح للوكيل:")
            return ENTERING_AGENT_NAME

        context.user_data['agent_name'] = agent_name
        await update.message.reply_text("أدخل معرف المستخدم للوكيل:")
        return ENTERING_AGENT_USER_ID

    async def handle_agent_user_id_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle agent user ID entry"""
        try:
            user_id = int(update.message.text.strip())

            # Check if user exists
            user_data = data_manager.get_user_details(user_id)
            if not user_data:
                await update.message.reply_text("❌ هذا المستخدم غير موجود في النظام.")
                return ENTERING_AGENT_USER_ID

            # Check if user is already an agent
            existing_agent = data_manager.get_agent_by_user_id(user_id)
            if existing_agent:
                await update.message.reply_text("❌ هذا المستخدم مسجل كوكيل بالفعل.")
                return ENTERING_AGENT_USER_ID

            context.user_data['agent_user_id'] = user_id
            await update.message.reply_text("أدخل نسبة الربح للوكيل (بالنسبة المئوية، مثال: 5 لـ 5%):")
            return ENTERING_AGENT_COMMISSION

        except ValueError:
            await update.message.reply_text("يرجى إدخال معرف مستخدم صحيح (رقم):")
            return ENTERING_AGENT_USER_ID

    async def handle_agent_commission_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle agent commission entry"""
        try:
            commission = float(update.message.text.strip())

            if commission < 0 or commission > 100:
                await update.message.reply_text("يرجى إدخال نسبة بين 0 و 100:")
                return ENTERING_AGENT_COMMISSION

            context.user_data['agent_commission'] = commission

            # Show confirmation
            agent_name = context.user_data['agent_name']
            user_id = context.user_data['agent_user_id']

            message = f"🤝 **تأكيد إضافة الوكيل**\n\n"
            message += f"الاسم: {agent_name}\n"
            message += f"معرف المستخدم: {user_id}\n"
            message += f"نسبة الربح: {commission}%\n\n"
            message += "هل تريد إضافة هذا الوكيل؟"

            keyboard = [
                [InlineKeyboardButton("✅ إضافة الوكيل", callback_data="confirm_add_agent")],
                [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_add_agent")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            return CONFIRMING_AGENT_ADD

        except ValueError:
            await update.message.reply_text("يرجى إدخال نسبة صحيحة:")
            return ENTERING_AGENT_COMMISSION

    async def handle_agent_add_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle agent addition confirmation"""
        query = update.callback_query
        await query.answer()

        if query.data == "cancel_add_agent":
            await query.edit_message_text("تم إلغاء إضافة الوكيل.")
            context.user_data.clear()
            return await self.show_agents_management(update, context)

        elif query.data == "confirm_add_agent":
            agent_name = context.user_data['agent_name']
            user_id = context.user_data['agent_user_id']
            commission = context.user_data['agent_commission']

            # Generate agent ID
            agent_id = f"agent_{user_id}"

            # Add agent
            data_manager.add_agent(agent_id, agent_name, user_id, commission)

            await query.edit_message_text(f"✅ تم إضافة الوكيل '{agent_name}' بنجاح!")

            # Notify the agent
            try:
                bot_name = data_manager.get_bot_name(english=False)
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🎉 تهانينا! تم تعيينك كوكيل في بوت {bot_name}\n\n"
                         f"👤 اسمك كوكيل: {agent_name}\n"
                         f"💰 نسبة الربح: {commission}%\n\n"
                         f"يمكنك الآن استخدام زر 'لوحة الوكيل' في القائمة الرئيسية"
                )
            except Exception as e:
                logger.error(f"Failed to notify new agent: {e}")

            context.user_data.clear()
            return MANAGING_AGENTS

    async def handle_agent_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle agent selection for actions"""
        text = update.message.text
        action = context.user_data.get('agent_action')

        if text == "⬅️ العودة":
            return await self.show_agents_management(update, context)

        # Find selected agent
        agents = data_manager.get_agents()
        selected_agent_id = None

        for agent_id, agent_data in agents.items():
            expected_text = f"{agent_data['name']} ({agent_data['commission_rate']}%)"
            if text == expected_text:
                selected_agent_id = agent_id
                break

        if not selected_agent_id:
            await update.message.reply_text("يرجى اختيار وكيل من القائمة.")
            return SELECTING_AGENT_TO_EDIT

        context.user_data['selected_agent_id'] = selected_agent_id
        agent_data = agents[selected_agent_id]

        if action == "edit_commission":
            await update.message.reply_text(
                f"الوكيل: {agent_data['name']}\n"
                f"النسبة الحالية: {agent_data['commission_rate']}%\n\n"
                "أدخل النسبة الجديدة:"
            )
            return EDITING_AGENT_COMMISSION

        elif action == "delete":
            message = f"⚠️ **تأكيد حذف الوكيل**\n\n"
            message += f"الوكيل: {agent_data['name']}\n"
            message += f"الأرباح المتراكمة: {agent_data['total_earnings']:,.2f} SYP\n"
            message += f"العمليات: {agent_data['total_orders']}\n\n"
            message += "هل أنت متأكد من حذف هذا الوكيل؟"

            keyboard = [
                [InlineKeyboardButton("✅ حذف الوكيل", callback_data=f"confirm_delete_agent_{selected_agent_id}")],
                [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_agent_action")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            return CONFIRMING_AGENT_DELETE

        elif action == "statistics":
            message = f"📊 **إحصائيات الوكيل**\n\n"
            message += f"👤 الاسم: {agent_data['name']}\n"
            message += f"🆔 معرف المستخدم: {agent_data['user_id']}\n"
            message += f"💰 نسبة الربح: {agent_data['commission_rate']}%\n"
            message += f"💵 صافي الأرباح: {agent_data['total_earnings']:,.2f} SYP\n"
            message += f"📦 عدد العمليات: {agent_data['total_orders']}\n"
            message += f"📅 تاريخ التسجيل: {datetime.fromisoformat(agent_data['created_at']).strftime('%Y-%m-%d')}\n"

            if agent_data['total_orders'] > 0:
                avg_per_order = agent_data['total_earnings'] / agent_data['total_orders']
                message += f"💱 متوسط الربح لكل عملية: {avg_per_order:,.2f} SYP"

            await update.message.reply_text(message, parse_mode='Markdown')
            return await self.show_agents_management(update, context)

        elif action == "balance_management":
            return await self.handle_agent_balance_management(update, context, agent_data, selected_agent_id)

        return MANAGING_AGENTS

    async def handle_agent_commission_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle agent commission editing"""
        try:
            new_commission = float(update.message.text.strip())

            if new_commission < 0 or new_commission > 100:
                await update.message.reply_text("يرجى إدخال نسبة بين 0 و 100:")
                return EDITING_AGENT_COMMISSION

            agent_id = context.user_data['selected_agent_id']
            agents = data_manager.get_agents()
            agent_data = agents[agent_id]

            message = f"✏️ **تأكيد تعديل النسبة**\n\n"
            message += f"الوكيل: {agent_data['name']}\n"
            message += f"النسبة القديمة: {agent_data['commission_rate']}%\n"
            message += f"النسبة الجديدة: {new_commission}%\n\n"
            message += "هل تريد تأكيد التعديل؟"

            context.user_data['new_commission'] = new_commission

            keyboard = [
                [InlineKeyboardButton("✅ تأكيد التعديل", callback_data=f"confirm_edit_agent_{agent_id}")],
                [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_agent_action")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            return CONFIRMING_AGENT_EDIT

        except ValueError:
            await update.message.reply_text("يرجى إدخال نسبة صحيحة:")
            return EDITING_AGENT_COMMISSION

    async def handle_withdrawal_fees_setting(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle withdrawal fees setting"""
        try:
            fees = float(update.message.text.strip())

            if fees < 0 or fees > 100:
                await update.message.reply_text("يرجى إدخال نسبة بين 0 و 100:")
                return SETTING_WITHDRAWAL_FEES

            data_manager.set_withdrawal_fees(fees)
            await update.message.reply_text(f"✅ تم تعيين رسوم السحب إلى {fees}%")

            return await self.show_agents_management(update, context)

        except ValueError:
            await update.message.reply_text("يرجى إدخال نسبة صحيحة:")
            return SETTING_WITHDRAWAL_FEES

    async def show_agents_balance_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show agents balance management interface"""
        agents = data_manager.get_agents()

        if not agents:
            await update.message.reply_text("لا يوجد وكلاء مسجلون.")
            return await self.show_agents_management(update, context)

        message = f"💳 **إدارة رصيد الوكلاء**\n\nاختر الوكيل:\n\n"

        keyboard = []
        for agent_id, agent_data in agents.items():
            earnings = agent_data.get('total_earnings', 0)
            button_text = f"{agent_data['name']} ({earnings:,.2f} SYP)"
            keyboard.append([KeyboardButton(button_text)])

        keyboard.append([KeyboardButton("⬅️ العودة")])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        context.user_data['agent_action'] = 'balance_management'
        return SELECTING_AGENT_TO_EDIT

    async def handle_agent_balance_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE, agent_data: Dict, agent_id: str) -> int:
        """Handle agent balance management actions"""
        withdrawal_fees = data_manager.get_withdrawal_fees()
        earnings = agent_data.get('total_earnings', 0)

        if earnings <= 0:
            await update.message.reply_text(f"❌ الوكيل {agent_data['name']} ليس لديه أرباح متاحة.")
            return await self.show_agents_balance_management(update, context)

        fees_amount = earnings * (withdrawal_fees / 100)
        net_amount = earnings - fees_amount

        message = f"💳 **إدارة رصيد الوكيل**\n\n"
        message += f"👤 الوكيل: {agent_data['name']}\n"
        message += f"🆔 معرف المستخدم: {agent_data['user_id']}\n"
        message += f"💵 إجمالي الأرباح: {earnings:,.2f} SYP\n"
        message += f"💳 رسوم السحب ({withdrawal_fees}%): {fees_amount:,.2f} SYP\n"
        message += f"💰 صافي المبلغ: {net_amount:,.2f} SYP\n\n"
        message += "اختر العملية:"

        keyboard = [
            [InlineKeyboardButton("💰 نقل للرصيد الرئيسي", callback_data=f"admin_transfer_balance_{agent_data['user_id']}_{int(net_amount)}_{int(earnings)}")],
            [InlineKeyboardButton("💸 تصفير الأرباح (سحب)", callback_data=f"admin_clear_earnings_{agent_data['user_id']}_{int(earnings)}")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_balance_management")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return CONFIRMING_AGENT_DELETE  # Reuse this state for balance management confirmations

    async def show_orders_channel_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show orders channel settings"""
        message = f"📢 **إعدادات قنوات الطلبات**\n\n"
        message += f"📦 قناة طلبات الشحن: `{ORDERS_CHANNEL}`\n"
        message += f"💰 قناة طلبات شحن الرصيد: `{BALANCE_REQUESTS_CHANNEL}`\n\n"
        message += f"يتم إرسال طلبات شحن التطبيقات والألعاب إلى القناة الأولى\n"
        message += f"وطلبات شحن الرصيد إلى القناة الثانية\n\n"
        message += f"لتغيير القنوات، قم بتعديل المتغيرات في الكود:\n"
        message += f"• ORDERS_CHANNEL للطلبات العادية\n"
        message += f"• BALANCE_REQUESTS_CHANNEL لطلبات شحن الرصيد\n\n"
        message += f"تأكد من إضافة البوت كمشرف في القنوات"

        keyboard = [
            [KeyboardButton("اختبار قناة الطلبات 🧪")],
            [KeyboardButton("اختبار قناة شحن الرصيد 💰")],
            [KeyboardButton("⬅️ العودة للوحة التحكم")]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return MANAGING_ORDERS_CHANNEL

    async def handle_orders_channel_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle orders channel settings actions"""
        text = update.message.text

        if text == "اختبار قناة الطلبات 🧪":
            test_message = f"🧪 **رسالة اختبار - قناة الطلبات**\n\n"
            test_message += f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            test_message += f"✅ قناة طلبات الشحن تعمل بشكل صحيح!"

            try:
                await context.bot.send_message(
                    chat_id=ORDERS_CHANNEL,
                    text=test_message,
                    parse_mode='Markdown'
                )
                await update.message.reply_text("✅ تم إرسال رسالة اختبار بنجاح لقناة الطلبات!")
            except Exception as e:
                await update.message.reply_text(f"❌ فشل في إرسال رسالة لقناة الطلبات: {str(e)}")
                logger.error(f"Test message to orders channel failed: {e}")

            return MANAGING_ORDERS_CHANNEL

        elif text == "اختبار قناة شحن الرصيد 💰":
            test_message = f"🧪 **رسالة اختبار - قناة شحن الرصيد**\n\n"
            test_message += f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            test_message += f"✅ قناة طلبات شحن الرصيد تعمل بشكل صحيح!"

            try:
                await context.bot.send_message(
                    chat_id=BALANCE_REQUESTS_CHANNEL,
                    text=test_message,
                    parse_mode='Markdown'
                )
                await update.message.reply_text("✅ تم إرسال رسالة اختبار بنجاح لقناة شحن الرصيد!")
            except Exception as e:
                await update.message.reply_text(f"❌ فشل في إرسال رسالة لقناة شحن الرصيد: {str(e)}")
                logger.error(f"Test message to balance requests channel failed: {e}")

            return MANAGING_ORDERS_CHANNEL

        elif text == "⬅️ العودة للوحة التحكم":
            return await self.show_admin_panel(update, context)

        else:
            await update.message.reply_text("يرجى اختيار خيار صحيح من القائمة.")
            return MANAGING_ORDERS_CHANNEL

    async def show_bulk_price_adjustment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Show bulk price adjustment menu"""
        message = "📈 **تعديل الأسعار الجماعي**\n\n"
        message += "يمكنك زيادة أو تقليل جميع الأسعار في البوت دفعة واحدة\n\n"
        message += "اختر نوع التعديل:"

        keyboard = [
            [KeyboardButton("زيادة مبلغ ثابت ➕")],
            [KeyboardButton("زيادة نسبة مئوية 📊")],
            [KeyboardButton("تقليل مبلغ ثابت ➖")],
            [KeyboardButton("تقليل نسبة مئوية 📉")],
            [KeyboardButton("⬅️ العودة للوحة التحكم")]
        ]

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

        return BULK_PRICE_ADJUSTMENT

    async def handle_bulk_price_adjustment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle bulk price adjustment type selection"""
        text = update.message.text

        if text == "زيادة مبلغ ثابت ➕":
            context.user_data['adjustment_type'] = 'increase_fixed'
            await update.message.reply_text("أدخل المبلغ المراد زيادته على جميع الأسعار (بـ SYP):")
            return ENTERING_ADJUSTMENT_VALUE

        elif text == "زيادة نسبة مئوية 📊":
            context.user_data['adjustment_type'] = 'increase_percentage'
            await update.message.reply_text("أدخل النسبة المئوية للزيادة (مثال: 10 لزيادة 10%):")
            return ENTERING_ADJUSTMENT_VALUE

        elif text == "تقليل مبلغ ثابت ➖":
            context.user_data['adjustment_type'] = 'decrease_fixed'
            await update.message.reply_text("أدخل المبلغ المراد تقليله من جميع الأسعار (بـ SYP):")
            return ENTERING_ADJUSTMENT_VALUE

        elif text == "تقليل نسبة مئوية 📉":
            context.user_data['adjustment_type'] = 'decrease_percentage'
            await update.message.reply_text("أدخل النسبة المئوية للتقليل (مثال: 15 لتقليل 15%):")
            return ENTERING_ADJUSTMENT_VALUE

        elif text == "⬅️ العودة للوحة التحكم":
            return await self.show_admin_panel(update, context)

        else:
            await update.message.reply_text("يرجى اختيار نوع التعديل من القائمة.")
            return BULK_PRICE_ADJUSTMENT

    async def handle_adjustment_value_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle adjustment value entry"""
        try:
            value = float(update.message.text.strip())
            adjustment_type = context.user_data.get('adjustment_type')

            if value <= 0:
                await update.message.reply_text("يرجى إدخال قيمة موجبة:")
                return ENTERING_ADJUSTMENT_VALUE

            if 'percentage' in adjustment_type and value > 100:
                await update.message.reply_text("النسبة المئوية لا يمكن أن تتجاوز 100%:")
                return ENTERING_ADJUSTMENT_VALUE

            context.user_data['adjustment_value'] = value

            # Calculate preview
            apps = data_manager.get_apps()
            games = data_manager.get_games()
            payments = data_manager.get_payments()

            total_categories = 0
            sample_changes = []

            # Count and sample from apps
            for app_id, app_data in apps.items():
                for cat_id, cat_data in app_data['categories'].items():
                    total_categories += 1
                    if len(sample_changes) < 3:  # Show max 3 samples
                        old_price = cat_data.get('price') or cat_data.get('price_per_unit', 0)
                        new_price = self._calculate_new_price(old_price, adjustment_type, value)
                        sample_changes.append({
                            'name': f"{app_data['name']} - {cat_data['name']}",
                            'old_price': old_price,
                            'new_price': new_price
                        })

            # Count and sample from games
            for game_id, game_data in games.items():
                for cat_id, cat_data in game_data['categories'].items():
                    total_categories += 1
                    if len(sample_changes) < 3:
                        old_price = cat_data.get('price') or cat_data.get('price_per_unit', 0)
                        new_price = self._calculate_new_price(old_price, adjustment_type, value)
                        sample_changes.append({
                            'name': f"{game_data['name']} - {cat_data['name']}",
                            'old_price': old_price,
                            'new_price': new_price
                        })

            # Count and sample from payments
            for service_id, service_data in payments.items():
                for cat_id, cat_data in service_data['categories'].items():
                    total_categories += 1
                    if len(sample_changes) < 3:
                        old_price = cat_data.get('price') or cat_data.get('price_per_unit', 0)
                        new_price = self._calculate_new_price(old_price, adjustment_type, value)
                        sample_changes.append({
                            'name': f"{service_data['name']} - {cat_data['name']}",
                            'old_price': old_price,
                            'new_price': new_price
                        })

            # Create confirmation message
            message = f"📈 **تأكيد التعديل الجماعي**\n\n"

            if adjustment_type == 'increase_fixed':
                message += f"نوع التعديل: زيادة مبلغ ثابت\n"
                message += f"المبلغ: +{value:,} SYP\n\n"
            elif adjustment_type == 'increase_percentage':
                message += f"نوع التعديل: زيادة نسبة مئوية\n"
                message += f"النسبة: +{value}%\n\n"
            elif adjustment_type == 'decrease_fixed':
                message += f"نوع التعديل: تقليل مبلغ ثابت\n"
                message += f"المبلغ: -{value:,} SYP\n\n"
            else:  # decrease_percentage
                message += f"نوع التعديل: تقليل نسبة مئوية\n"
                message += f"النسبة: -{value}%\n\n"

            message += f"عدد الفئات المتأثرة: {total_categories}\n\n"

            if sample_changes:
                message += "أمثلة على التغييرات:\n"
                for change in sample_changes:
                    message += f"• {change['name']}\n"
                    message += f"  السعر القديم: {change['old_price']:,.2f} SYP\n"
                    message += f"  السعر الجديد: {change['new_price']:,.2f} SYP\n\n"

            message += "⚠️ **تحذير**: هذا الإجراء سيؤثر على جميع الأسعار في البوت ولا يمكن التراجع عنه!\n\n"
            message += "هل تريد المتابعة؟"

            keyboard = [
                [InlineKeyboardButton("✅ تأكيد التعديل", callback_data="confirm_bulk_adjustment")],
                [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_bulk_adjustment")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')

            return CONFIRMING_BULK_ADJUSTMENT

        except ValueError:
            await update.message.reply_text("يرجى إدخال قيمة صحيحة:")
            return ENTERING_ADJUSTMENT_VALUE

    def _calculate_new_price(self, old_price: float, adjustment_type: str, value: float) -> float:
        """Calculate new price based on adjustment type"""
        if adjustment_type == 'increase_fixed':
            return old_price + value
        elif adjustment_type == 'increase_percentage':
            return old_price * (1 + value / 100)
        elif adjustment_type == 'decrease_fixed':
            return max(1, old_price - value)  # Minimum price is 1
        else:  # decrease_percentage
            return max(1, old_price * (1 - value / 100))  # Minimum price is 1

    async def handle_bulk_adjustment_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle bulk adjustment confirmation"""
        query = update.callback_query
        await query.answer()

        if query.data == "cancel_bulk_adjustment":
            await query.edit_message_text("تم إلغاء التعديل الجماعي.")
            context.user_data.clear()
            return await self.show_bulk_price_adjustment(update, context)

        elif query.data == "confirm_bulk_adjustment":
            adjustment_type = context.user_data.get('adjustment_type')
            value = context.user_data.get('adjustment_value')

            await query.edit_message_text("⏳ جاري تطبيق التعديلات...")

            try:
                updated_count = 0

                # Update apps
                apps = data_manager.get_apps()
                for app_id, app_data in apps.items():
                    for cat_id, cat_data in app_data['categories'].items():
                        if 'price' in cat_data:
                            old_price = cat_data['price']
                            new_price = self._calculate_new_price(old_price, adjustment_type, value)
                            apps[app_id]['categories'][cat_id]['price'] = int(new_price)
                            updated_count += 1
                        elif 'price_per_unit' in cat_data:
                            old_price = cat_data['price_per_unit']
                            new_price = self._calculate_new_price(old_price, adjustment_type, value)
                            apps[app_id]['categories'][cat_id]['price_per_unit'] = new_price
                            updated_count += 1

                data_manager._save_json(data_manager.apps_file, apps)

                # Update games
                games = data_manager.get_games()
                for game_id, game_data in games.items():
                    for cat_id, cat_data in game_data['categories'].items():
                        if 'price' in cat_data:
                            old_price = cat_data['price']
                            new_price = self._calculate_new_price(old_price, adjustment_type, value)
                            games[game_id]['categories'][cat_id]['price'] = int(new_price)
                            updated_count += 1
                        elif 'price_per_unit' in cat_data:
                            old_price = cat_data['price_per_unit']
                            new_price = self._calculate_new_price(old_price, adjustment_type, value)
                            games[game_id]['categories'][cat_id]['price_per_unit'] = new_price
                            updated_count += 1

                data_manager._save_json(data_manager.games_file, games)

                # Update payment services
                settings = data_manager._load_json(data_manager.settings_file)
                payments = settings.get('payment_services', {})
                for service_id, service_data in payments.items():
                    for cat_id, cat_data in service_data['categories'].items():
                        if 'price' in cat_data:
                            old_price = cat_data['price']
                            new_price = self._calculate_new_price(old_price, adjustment_type, value)
                            settings['payment_services'][service_id]['categories'][cat_id]['price'] = int(new_price)
                            updated_count += 1
                        elif 'price_per_unit' in cat_data:
                            old_price = cat_data['price_per_unit']
                            new_price = self._calculate_new_price(old_price, adjustment_type, value)
                            settings['payment_services'][service_id]['categories'][cat_id]['price_per_unit'] = new_price
                            updated_count += 1

                data_manager._save_json(data_manager.settings_file, settings)

                # Success message
                success_message = f"✅ **تم تطبيق التعديل الجماعي بنجاح!**\n\n"
                success_message += f"عدد الفئات المحدثة: {updated_count}\n"

                if adjustment_type == 'increase_fixed':
                    success_message += f"تم زيادة {value:,} SYP على جميع الأسعار"
                elif adjustment_type == 'increase_percentage':
                    success_message += f"تم زيادة {value}% على جميع الأسعار"
                elif adjustment_type == 'decrease_fixed':
                    success_message += f"تم تقليل {value:,} SYP من جميع الأسعار"
                else:  # decrease_percentage
                    success_message += f"تم تقليل {value}% من جميع الأسعار"

                success_message += f"\n📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

                await context.bot.edit_message_text(
                    chat_id=query.message.chat_id,
                    message_id=query.message.message_id,
                    text=success_message,
                    parse_mode='Markdown'
                )

                context.user_data.clear()
                return BULK_PRICE_ADJUSTMENT

            except Exception as e:
                error_message = f"❌ حدث خطأ أثناء تطبيق التعديلات: {str(e)}"
                logger.error(f"Bulk price adjustment error: {e}")

                await context.bot.edit_message_text(
                    chat_id=query.message.chat_id,
                    message_id=query.message.message_id,
                    text=error_message
                )

                context.user_data.clear()
                return BULK_PRICE_ADJUSTMENT

    async def show_agent_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE, agent_data: Dict) -> int:
        """Show agent panel"""
        message = f"🤝 لوحة الوكيل\n\n"
        message += f"👤 اسم الوكيل: {agent_data['name']}\n"
        message += f"🆔 معرف الوكيل: {agent_data['agent_id']}\n"
        message += f"💰 نسبة الربح: {agent_data['commission_rate']}%\n"
        message += f"💵 صافي الأرباح: {agent_data['total_earnings']:,.2f} SYP\n"
        message += f"📦 عدد العمليات: {agent_data['total_orders']}\n\n"

        if agent_data['total_earnings'] > 0:
            withdrawal_fees = data_manager.get_withdrawal_fees()
            fees_amount = agent_data['total_earnings'] * (withdrawal_fees / 100)
            net_amount = agent_data['total_earnings'] - fees_amount

            message += f"💳 رسوم السحب: {withdrawal_fees}% ({fees_amount:,.2f} SYP)\n"
            message += f"💰 صافي المبلغ بعد الرسوم: {net_amount:,.2f} SYP\n\n"

        keyboard = []

        if agent_data['total_earnings'] > 0:
            keyboard.append([KeyboardButton("طلب سحب الأرباح 💸")])

        keyboard.append([KeyboardButton("⬅️ العودة للقائمة الرئيسية")])

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        # Send message without Markdown to avoid parsing errors
        await update.message.reply_text(message, reply_markup=reply_markup)

        return AGENT_PANEL

    async def handle_agent_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle agent panel actions"""
        text = update.message.text
        user_id = update.effective_user.id

        if text == "طلب سحب الأرباح 💸":
            agent_data = data_manager.get_agent_by_user_id(user_id)
            if not agent_data:
                await update.message.reply_text("❌ غير مصرح لك بهذه العملية.")
                return MAIN_MENU

            if agent_data['total_earnings'] <= 0:
                await update.message.reply_text("❌ لا توجد أرباح متاحة للسحب.")
                return AGENT_PANEL

            withdrawal_fees = data_manager.get_withdrawal_fees()
            fees_amount = agent_data['total_earnings'] * (withdrawal_fees / 100)
            net_amount = agent_data['total_earnings'] - fees_amount

            message = f"💸 **طلب سحب الأرباح**\n\n"
            message += f"💵 إجمالي الأرباح: {agent_data['total_earnings']:,.2f} SYP\n"
            message += f"💳 رسوم السحب ({withdrawal_fees}%): {fees_amount:,.2f} SYP\n"
            message += f"💰 صافي المبلغ: {net_amount:,.2f} SYP\n\n"
            message += "اختر نوع السحب:"

            keyboard = [
                [InlineKeyboardButton("💰 تحويل للرصيد الرئيسي", callback_data="direct_transfer_to_balance")],
                [InlineKeyboardButton("💸 سحب خارجي (يتطلب موافقة)", callback_data="external_withdrawal_request")],
                [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_withdrawal")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
            return CONFIRMING_WITHDRAWAL_REQUEST

        elif text == "⬅️ العودة للقائمة الرئيسية":
            return await self.start(update, context)

        else:
            await update.message.reply_text("يرجى اختيار خيار صحيح من القائمة.")
            return AGENT_PANEL

    async def handle_withdrawal_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle withdrawal confirmation"""
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id

        if query.data == "cancel_withdrawal":
            await query.edit_message_text("تم إلغاء طلب السحب.")
            agent_data = data_manager.get_agent_by_user_id(user_id)
            return await self.show_agent_panel(update, context, agent_data)

        elif query.data == "direct_transfer_to_balance":
            # Direct transfer to main balance with fees
            agent_data = data_manager.get_agent_by_user_id(user_id)
            if not agent_data:
                await query.edit_message_text("❌ خطأ في النظام.")
                return MAIN_MENU

            if agent_data['total_earnings'] <= 0:
                await query.edit_message_text("❌ لا توجد أرباح متاحة للسحب.")
                return AGENT_PANEL

            # Calculate net amount after fees
            withdrawal_fees = data_manager.get_withdrawal_fees()
            fees_amount = agent_data['total_earnings'] * (withdrawal_fees / 100)
            net_amount = agent_data['total_earnings'] - fees_amount

            # Clear agent earnings and add to main balance
            data_manager.withdraw_agent_earnings(user_id)
            data_manager.update_user_balance(user_id, int(net_amount))

            message = f"✅ **تم تحويل الأرباح بنجاح!**\n\n"
            message += f"💵 المبلغ الأصلي: {agent_data['total_earnings']:,.2f} SYP\n"
            message += f"💳 الرسوم ({withdrawal_fees}%): {fees_amount:,.2f} SYP\n"
            message += f"💰 صافي المبلغ المحول: {net_amount:,.2f} SYP\n\n"
            message += f"تم إضافة المبلغ إلى رصيد حسابك الرئيسي\n"
            message += f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            await query.edit_message_text(message, parse_mode='Markdown')
            return AGENT_PANEL

        elif query.data == "external_withdrawal_request":
            # External withdrawal request (requires admin approval)
            agent_data = data_manager.get_agent_by_user_id(user_id)
            if not agent_data:
                await query.edit_message_text("❌ خطأ في النظام.")
                return MAIN_MENU

            if agent_data['total_earnings'] <= 0:
                await query.edit_message_text("❌ لا توجد أرباح متاحة للسحب.")
                return AGENT_PANEL

            # Calculate net amount after fees
            withdrawal_fees = data_manager.get_withdrawal_fees()
            fees_amount = agent_data['total_earnings'] * (withdrawal_fees / 100)
            net_amount = agent_data['total_earnings'] - fees_amount

            # Store withdrawal data temporarily
            withdrawal_amount = agent_data['total_earnings']

            # Clear agent earnings
            data_manager.withdraw_agent_earnings(user_id)

            message = f"📤 **تم إرسال طلب السحب الخارجي!**\n\n"
            message += f"💵 المبلغ الأصلي: {withdrawal_amount:,.2f} SYP\n"
            message += f"💳 الرسوم ({withdrawal_fees}%): {fees_amount:,.2f} SYP\n"
            message += f"💰 صافي المبلغ: {net_amount:,.2f} SYP\n\n"
            message += f"📩 تم إرسال الطلب للإدارة وسيتم المراجعة قريباً\n"
            message += f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            await query.edit_message_text(message, parse_mode='Markdown')

            # Send request to admin
            try:
                admin_message = f"💸 **طلب سحب خارجي من وكيل**\n\n"
                admin_message += f"👤 الوكيل: {agent_data['name']}\n"
                admin_message += f"🆔 المستخدم: {user_id}\n"
                admin_message += f"💵 المبلغ الأصلي: {withdrawal_amount:,.2f} SYP\n"
                admin_message += f"💳 الرسوم ({withdrawal_fees}%): {fees_amount:,.2f} SYP\n"
                admin_message += f"💰 صافي المبلغ: {net_amount:,.2f} SYP\n"
                admin_message += f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                admin_message += f"⚠️ **تم تصفير أرباح الوكيل بالفعل**"

                keyboard = [
                    [InlineKeyboardButton("✅ موافقة على السحب", callback_data=f"approve_external_withdrawal_{user_id}_{int(net_amount)}")],
                    [InlineKeyboardButton("❌ رفض الطلب", callback_data=f"reject_withdrawal_{user_id}_{int(withdrawal_amount)}")]
                ]

                reply_markup = InlineKeyboardMarkup(keyboard)

                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=admin_message,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to notify admin about external withdrawal: {e}")
                # Return earnings if admin notification failed
                data_manager.add_agent_earnings(user_id, withdrawal_amount)
                await context.bot.send_message(
                    chat_id=user_id,
                    text="❌ حدث خطأ في إرسال الطلب. تم إرجاع أرباحك."
                )

            return AGENT_PANEL

    async def handle_agent_callbacks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle agent-related callbacks"""
        query = update.callback_query
        await query.answer()

        if not update.effective_user.id == ADMIN_ID:
            return

        data = query.data

        if data.startswith("confirm_delete_agent_"):
            agent_id = data.replace("confirm_delete_agent_", "")
            agents = data_manager.get_agents()
            agent_data = agents.get(agent_id)

            if agent_data:
                success = data_manager.delete_agent(agent_id)
                if success:
                    await query.edit_message_text(f"✅ تم حذف الوكيل '{agent_data['name']}' بنجاح!")

                    # Notify the ex-agent
                    try:
                        bot_name = data_manager.get_bot_name(english=False)
                        await context.bot.send_message(
                            chat_id=agent_data['user_id'],
                            text=f"📢 تم إلغاء تعيينك كوكيل في بوت {bot_name}"
                        )
                    except:
                        pass
                else:
                    await query.edit_message_text("❌ فشل في حذف الوكيل.")
            else:
                await query.edit_message_text("❌ الوكيل غير موجود.")

        elif data.startswith("confirm_edit_agent_"):
            agent_id = data.replace("confirm_edit_agent_", "")
            new_commission = context.user_data.get('new_commission')

            success = data_manager.update_agent(agent_id, {"commission_rate": new_commission})
            if success:
                await query.edit_message_text(f"✅ تم تعديل نسبة الربح إلى {new_commission}%")
            else:
                await query.edit_message_text("❌ فشل في تعديل البيانات.")

            context.user_data.clear()

        elif data in ["cancel_add_agent", "cancel_agent_action", "cancel_balance_management"]:
            await query.edit_message_text("تم الإلغاء.")
            context.user_data.clear()

        elif data.startswith("admin_transfer_balance_"):
            # Extract user_id, net_amount, and original_earnings from callback data
            parts = data.split('_')
            user_id = int(parts[3])
            net_amount = int(parts[4])
            original_earnings = int(parts[5])

            # Clear agent earnings and add to user balance
            data_manager.withdraw_agent_earnings(user_id)
            data_manager.update_user_balance(user_id, net_amount)

            await query.edit_message_text(
                f"✅ **تم نقل الأرباح بنجاح!**\n\n"
                f"💵 المبلغ الأصلي: {original_earnings:,} SYP\n"
                f"💰 المبلغ المحول: {net_amount:,} SYP\n"
                f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                parse_mode='Markdown'
            )

            # Notify agent
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"💰 **تم نقل أرباحك للرصيد الرئيسي!**\n\n"
                         f"💵 المبلغ الأصلي: {original_earnings:,} SYP\n"
                         f"💰 المبلغ المحول: {net_amount:,} SYP\n"
                         f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to notify agent about balance transfer: {e}")

        elif data.startswith("admin_clear_earnings_"):
            # Extract user_id and earnings amount from callback data
            parts = data.split('_')
            user_id = int(parts[3])
            earnings_amount = int(parts[4])

            # Clear agent earnings
            data_manager.withdraw_agent_earnings(user_id)

            await query.edit_message_text(
                f"🗑️ **تم تصفير الأرباح بنجاح!**\n\n"
                f"💵 المبلغ المحذوف: {earnings_amount:,} SYP\n"
                f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                parse_mode='Markdown'
            )

            # Notify agent
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📢 **تم سحب أرباحك**\n\n"
                         f"💸 المبلغ المسحوب: {earnings_amount:,} SYP\n"
                         f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to notify agent about earnings clearing: {e}")

    async def handle_user_action_callbacks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user action callbacks"""
        query = update.callback_query
        await query.answer()

        if not update.effective_user.id == ADMIN_ID:
            return

        data = query.data

        if data.startswith("confirm_action_"):
            parts = data.split('_')
            action = parts[2]
            user_id = int(parts[3])

            success = False
            result_message = ""

            if action == "ban":
                success = data_manager.ban_user(user_id)
                result_message = "✅ تم حظر المستخدم بنجاح!" if success else "❌ فشل في حظر المستخدم."

            elif action == "unban":
                success = data_manager.unban_user(user_id)
                result_message = "✅ تم فك حظر المستخدم بنجاح!" if success else "❌ فشل في فك حظر المستخدم."

            elif action == "unfreeze":
                success = data_manager.unfreeze_user(user_id)
                result_message = "✅ تم فك تجميد المستخدم بنجاح!" if success else "❌ فشل في فك تجميد المستخدم."

            elif action == "delete":
                success = data_manager.delete_user(user_id)
                result_message = "✅ تم حذف المستخدم بنجاح!" if success else "❌ فشل في حذف المستخدم."

            if result_message:
                await query.edit_message_text(result_message)

        elif data.startswith("confirm_freeze_"):
            user_id = int(data.split('_')[2])
            duration = context.user_data.get('freeze_duration')

            success = data_manager.freeze_user(user_id, duration)
            if success:
                freeze_until = datetime.now() + timedelta(minutes=duration)
                result_message = f"✅ تم تجميد المستخدم بنجاح!\n❄️ سينتهي التجميد في: {freeze_until.strftime('%Y-%m-%d %H:%M:%S')}"

                # Notify user about freeze
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"❄️ تم تجميد حسابك حتى: {freeze_until.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                except:
                    pass
            else:
                result_message = "❌ فشل في تجميد المستخدم."

            await query.edit_message_text(result_message)
            context.user_data.clear()

        elif data.startswith("send_private_message_"):
            user_id = int(data.split('_')[3])
            message_text = context.user_data.get('private_message_text')

            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message_text,
                    parse_mode='Markdown'
                )
                result_message = f"✅ تم إرسال الرسالة بنجاح للمستخدم `{user_id}`"
            except Exception as e:
                result_message = f"❌ فشل في إرسال الرسالة: {str(e)}"
                logger.error(f"Failed to send private message to {user_id}: {e}")

            await query.edit_message_text(result_message, parse_mode='Markdown')
            context.user_data.clear()

        elif data in ["cancel_user_action", "cancel_private_message", "close_user_details"]:
            await query.edit_message_text("تم الإلغاء.")
            context.user_data.clear()

    async def handle_payment_service_order_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle payment service order confirmation"""
        query = update.callback_query
        await query.answer()

        if query.data == "cancel_payment_service_order":
            await query.edit_message_text("تم إلغاء الطلب.")
            context.user_data.clear()
            return MAIN_MENU

        elif query.data == "confirm_payment_service_order":
            service_id = context.user_data.get('selected_payment_service')
            category_id = context.user_data.get('selected_payment_category')
            payments = data_manager.get_payments()

            service_data = payments.get(service_id)
            category_data = service_data['categories'].get(category_id)

            if not category_data:
                await query.edit_message_text("❌ الخدمة غير متاحة.")
                return MAIN_MENU

            user = update.effective_user
            user_data = data_manager.get_user(user.id)

            # Check if it's quantity-based pricing
            pricing_type = category_data.get('pricing_type', 'fixed')
            final_price = 0

            if pricing_type == 'quantity':
                quantity = context.user_data.get('quantity', 1)
                final_price = context.user_data.get('final_price', category_data['price_per_unit'] * quantity)
            else:
                final_price = category_data['price']

            # Double check balance
            if user_data['balance'] < final_price:
                await query.edit_message_text("❌ رصيد حسابك غير كافي.")
                return MAIN_MENU

            # Deduct balance
            data_manager.update_user_balance(user.id, -final_price)

            # Check if user is an agent and add commission
            agent_data = data_manager.get_agent_by_user_id(user.id)
            if agent_data:
                commission_amount = final_price * (agent_data['commission_rate'] / 100)
                data_manager.add_agent_earnings(user.id, commission_amount)

            # Generate order ID
            order_id = generate_order_id()

            # Create order record
            order_data = {
                "order_id": order_id,
                "user_id": user.id,
                "username": user.username or user.first_name,
                "service_type": "payment_service",
                "service_name": service_data['name'],
                "category_name": category_data['name'],
                "price": final_price,
                "pricing_type": pricing_type,
                "quantity": context.user_data.get('quantity', 1) if pricing_type == 'quantity' else 1,
                "account_id": context.user_data.get('account_id', ''),
                "input_type": category_data['input_type'],
                "input_data": context.user_data.get('payment_input_data', ''),
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "status": "قيد المعالجة"
            }

            # Save order
            data_manager.save_order(order_data)

            # Send confirmation to user
            confirmation_message = f"✅ **تم تأكيد طلب الخدمة بنجاح!**\n\n"
            confirmation_message += f"📱 القسم: مدفوعات\n\n"
            confirmation_message += f"🎮 الخدمة: {service_data['name']}\n\n"
            confirmation_message += f"🏷️ الفئة: {category_data['name']}\n\n"

            if pricing_type == 'quantity':
                confirmation_message += f"📊 الكمية: {context.user_data.get('quantity', 1)}\n\n"
                confirmation_message += f"💰 السعر لكل وحدة: {category_data['price_per_unit']:,} SYP\n\n"

            confirmation_message += f"💰 المبلغ الإجمالي: {final_price:,.2f} SYP\n\n"

            if category_data['input_type'] != 'none':
                confirmation_message += f"📝 {category_data['input_label']}: {context.user_data.get('payment_input_data')}\n\n"

            confirmation_message += f"🆔 رقم الطلب: {order_id}\n\n"
            confirmation_message += f"📅 التاريخ: {order_data['timestamp']}\n\n"
            confirmation_message += f"📊 الحالة: قيد المعالجة\n\n"
            confirmation_message += f"سيتم معالجة طلبك قريباً وسيتم إشعارك بالتحديثات\n\n"
            confirmation_message += f"💸 رصيدك الحالي: {user_data['balance'] - final_price:,.2f} SYP"

            await query.edit_message_text(confirmation_message, parse_mode='Markdown')

            # Notify admin with multiple format attempts
            def escape_markdown_v2(text):
                special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
                for char in special_chars:
                    text = str(text).replace(char, f'\\{char}')
                return text

            keyboard = [
                [InlineKeyboardButton("✅ تم التنفيذ", callback_data=f"complete_payment_order_{order_id}")],
                [InlineKeyboardButton("❌ مشكلة في الطلب", callback_data=f"reject_payment_order_{order_id}")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            # Try multiple formatting approaches
            max_attempts = 4
            admin_notification_sent = False

            for attempt in range(max_attempts):
                try:
                    if attempt == 0:
                        # First attempt with MarkdownV2
                        admin_message = f"🌟 طلб خدمة مدفوعات جديد\n\n"
                        admin_message += f"👤 المستخدم: @{escape_markdown_v2(user.username or user.first_name)} (`{user.id}`)\n"
                        admin_message += f"🌟 الخدمة: {escape_markdown_v2(service_data['name'])}\n"
                        admin_message += f"📦 الفئة: {escape_markdown_v2(category_data['name'])}\n"

                        if pricing_type == 'quantity':
                            admin_message += f"📊 الكمية: `{context.user_data.get('quantity', 1)}`\n"
                            admin_message += f"💰 السعر لكل وحدة: {category_data['price_per_unit']:,} SYP\n"

                        admin_message += f"💰 المبلغ الإجمالي: {final_price:,.2f} SYP\n"

                        if category_data['input_type'] != 'none':
                            admin_message += f"📝 {escape_markdown_v2(category_data['input_label'])}: `{escape_markdown_v2(context.user_data.get('payment_input_data', ''))}`\n"

                        admin_message += f"🆔 رقم الطلب: `{order_id}`\n"
                        admin_message += f"📅 التاريخ: {escape_markdown_v2(order_data['timestamp'])}\n"
                        admin_message += f"📊 الحالة: قيد المعالجة"

                        await context.bot.send_message(
                            chat_id=ADMIN_ID,
                            text=admin_message,
                            reply_markup=reply_markup,
                            parse_mode='MarkdownV2'
                        )
                    elif attempt == 1:
                        # Second attempt with HTML
                        admin_message = f"🌟 طلب خدمة مدفوعات جديد\n\n"
                        admin_message += f"👤 المستخدم: @{user.username or user.first_name} (<code>{user.id}</code>)\n"
                        admin_message += f"🌟 الخدمة: {service_data['name']}\n"
                        admin_message += f"📦 الفئة: {category_data['name']}\n"

                        if pricing_type == 'quantity':
                            admin_message += f"📊 الكمية: <code>{context.user_data.get('quantity', 1)}</code>\n"
                            admin_message += f"💰 السعر لكل وحدة: {category_data['price_per_unit']:,} SYP\n"

                        admin_message += f"💰 المبلغ الإجمالي: {final_price:,.2f} SYP\n"

                        if category_data['input_type'] != 'none':
                            admin_message += f"📝 {category_data['input_label']}: <code>{context.user_data.get('payment_input_data', '')}</code>\n"

                        admin_message += f"🆔 رقم الطلب: <code>{order_id}</code>\n"
                        admin_message += f"📅 التاريخ: {order_data['timestamp']}\n"
                        admin_message += f"📊 الحالة: قيد المعالجة"

                        await context.bot.send_message(
                            chat_id=ADMIN_ID,
                            text=admin_message,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
                    elif attempt == 2:
                        # Third attempt with basic Markdown
                        admin_message = f"🌟 طلب خدمة مدفوعات جديد\n\n"
                        admin_message += f"👤 المستخدم: @{user.username or user.first_name} (`{user.id}`)\n"
                        admin_message += f"🌟 الخدمة: {service_data['name']}\n"
                        admin_message += f"📦 الفئة: {category_data['name']}\n"

                        if pricing_type == 'quantity':
                            admin_message += f"📊 الكمية: `{context.user_data.get('quantity', 1)}`\n"
                            admin_message += f"💰 السعر لكل وحدة: {category_data['price_per_unit']:,} SYP\n"

                        admin_message += f"💰 المبلغ الإجمالي: {final_price:,.2f} SYP\n"

                        if category_data['input_type'] != 'none':
                            admin_message += f"📝 {category_data['input_label']}: `{context.user_data.get('payment_input_data', '')}`\n"

                        admin_message += f"🆔 رقم الطلب: `{order_id}`\n"
                        admin_message += f"📅 التاريخ: {order_data['timestamp']}\n"
                        admin_message += f"📊 الحالة: قيد المعالجة"

                        await context.bot.send_message(
                            chat_id=ADMIN_ID,
                            text=admin_message,
                            reply_markup=reply_markup,
                            parse_mode='Markdown'
                        )
                    else:
                        # Fourth attempt without formatting
                        admin_message = f"🌟 طلب خدمة مدفوعات جديد\n\n"
                        admin_message += f"👤 المستخدم: @{user.username or user.first_name} ({user.id})\n"
                        admin_message += f"🌟 الخدمة: {service_data['name']}\n"
                        admin_message += f"📦 الفئة: {category_data['name']}\n"

                        if pricing_type == 'quantity':
                            admin_message += f"📊 الكمية: {context.user_data.get('quantity', 1)}\n"
                            admin_message += f"💰 السعر لكل وحدة: {category_data['price_per_unit']:,} SYP\n"

                        admin_message += f"💰 المبلغ الإجمالي: {final_price:,.2f} SYP\n"

                        if category_data['input_type'] != 'none':
                            admin_message += f"📝 {category_data['input_label']}: {context.user_data.get('payment_input_data', '')}\n"

                        admin_message += f"🆔 رقم الطلب: {order_id}\n"
                        admin_message += f"📅 التاريخ: {order_data['timestamp']}\n"
                        admin_message += f"📊 الحالة: قيد المعالجة"

                        await context.bot.send_message(
                            chat_id=ADMIN_ID,
                            text=admin_message,
                            reply_markup=reply_markup
                        )

                    admin_notification_sent = True
                    logger.info(f"Payment service admin notification sent successfully on attempt {attempt + 1}")
                    break
                except Exception as e:
                    logger.error(f"Failed to notify admin about payment service order (attempt {attempt + 1}): {e}")
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(2)

            if not admin_notification_sent:
                logger.critical(f"CRITICAL: Failed to notify admin about payment service order {order_id} after {max_attempts} attempts")

            context.user_data.clear()
            return MAIN_MENU

    async def handle_referral_toggle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle referral system on/off"""
        if not data_manager.is_user_admin(update.effective_user.id):
            await update.message.reply_text("غير مسموح لك بالوصول لهذه الخدمة.")
            return

        referral_settings = data_manager.get_referral_settings()
        current_status = referral_settings["enabled"]
        new_status = not current_status

        data_manager.set_referral_settings(enabled=new_status)

        status_text = "مفعل ✅" if new_status else "معطل ❌"
        await update.message.reply_text(
            f"✅ تم تغيير حالة نظام الإحالة بنجاح!\n\nالحالة الجديدة: {status_text}",
            parse_mode='Markdown'
        )

    async def handle_referral_rates(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Update referral commission rates"""
        if not data_manager.is_user_admin(update.effective_user.id):
            await update.message.reply_text("غير مسموح لك بالوصول لهذه الخدمة.")
            return

        if not context.args or len(context.args) != 2:
            await update.message.reply_text(
                "⚠️ الاستخدام الصحيح:\n/referral_rates <نسبة_المستوى_الأول> <نسبة_المستوى_الثاني>\n\nمثال:\n/referral_rates 1.0 0.5"
            )
            return

        try:
            level_1 = float(context.args[0])
            level_2 = float(context.args[1])

            if level_1 < 0 or level_1 > 100 or level_2 < 0 or level_2 > 100:
                await update.message.reply_text("⚠️ النسب يجب أن تكون بين 0 و 100")
                return

            data_manager.set_referral_settings(level_1=level_1, level_2=level_2)

            await update.message.reply_text(
                f"✅ تم تحديث نسب العمولات بنجاح!\n\n"
                f"💰 نسبة المستوى الأول: **{level_1}%**\n"
                f"💵 نسبة المستوى الثاني: **{level_2}%**",
                parse_mode='Markdown'
            )
        except ValueError:
            await update.message.reply_text("⚠️ يرجى إدخال أرقام صحيحة للنسب")

    async def handle_viewing_top_referrers(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        text = update.message.text

        if text == "⬅️ العودة لإدارة الإحالات":
            return await self.show_referral_management(update, context)

        return VIEWING_TOP_REFERRERS

    async def handle_viewing_referral_transactions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        text = update.message.text

        if text == "⬅️ العودة لإدارة الإحالات":
            return await self.show_referral_management(update, context)

        return VIEWING_REFERRAL_TRANSACTIONS

    async def handle_entering_referral_rates(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        text = update.message.text

        if text == "⬅️ إلغاء":
            return await self.show_referral_management(update, context)

        try:
            parts = text.strip().split()
            if len(parts) != 2:
                await update.message.reply_text(
                    "⚠️ صيغة خاطئة. أرسل النسب بالصيغة التالية:\n`نسبة_المستوى_الأول نسبة_المستوى_الثاني`\n\nمثال: `1.5 0.75`",
                    parse_mode='Markdown'
                )
                return ENTERING_REFERRAL_RATES

            level_1 = float(parts[0])
            level_2 = float(parts[1])

            if level_1 < 0 or level_1 > 100 or level_2 < 0 or level_2 > 100:
                await update.message.reply_text("⚠️ النسب يجب أن تكون بين 0 و 100")
                return ENTERING_REFERRAL_RATES

            data_manager.set_referral_settings(level_1=level_1, level_2=level_2)

            await update.message.reply_text(
                f"✅ تم تحديث نسب العمولات بنجاح!\n\n"
                f"💰 نسبة المستوى الأول: **{level_1}%**\n"
                f"💵 نسبة المستوى الثاني: **{level_2}%**",
                parse_mode='Markdown'
            )

            return await self.show_referral_management(update, context)

        except ValueError:
            await update.message.reply_text("⚠️ يرجى إدخال أرقام صحيحة للنسب")
            return ENTERING_REFERRAL_RATES

    async def handle_entering_referral_user_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        text = update.message.text

        try:
            input_val = text.strip()

            user = None
            user_id = None
            if input_val.startswith('REF_'):
                referral_id = int(input_val.replace('REF_', ''))
                user_info = data_manager.get_user_by_referral_id(referral_id)
                if user_info:
                    user_id = user_info['user_id']
                    user = user_info['data']
            else:
                user_id = int(input_val)
                user = data_manager.get_user(user_id)

            if not user or user_id is None:
                await update.message.reply_text("❌ لم يتم العثور على المستخدم")
                return MANAGING_REFERRALS

            context.user_data['edit_referral_user_id'] = user_id

            referral_stats = data_manager.get_referral_stats(user_id)

            message = f"👤 <b>بيانات الإحالة للمستخدم</b>\n\n"
            message += f"🆔 User ID: <code>{user_id}</code>\n"
            message += f"🎫 Referral ID: <b>REF_{referral_stats['referral_id']}</b>\n\n"
            message += f"شارة الحساب: {referral_stats['badge']}\n"
            message += f"👥 عدد الإحالات: {referral_stats['referrals_count']}\n"
            message += f"⚡ إحالات فعالة: {referral_stats['active_referrals_count']}\n"
            message += f"💰 أرباح حالية: {referral_stats['earnings']:,.2f} SYP\n\n"
            message += "اختر العملية:"

            keyboard = [
                [KeyboardButton("تعديل عدد الإحالات 📊"), KeyboardButton("تعديل الأرباح 💰")],
                [KeyboardButton("⬅️ العودة لإدارة الإحالات")]
            ]

            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')

            return EDITING_USER_REFERRAL_DATA

        except ValueError:
            await update.message.reply_text("⚠️ يرجى إدخال User ID صحيح أو رقم إحالة (REF_XXX)")
            return ENTERING_REFERRAL_USER_ID

    async def handle_editing_user_referral_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        text = update.message.text

        if text == "⬅️ العودة لإدارة الإحالات":
            context.user_data.pop('edit_referral_user_id', None)
            return await self.show_referral_management(update, context)

        elif text == "تعديل عدد الإحالات 📊":
            await update.message.reply_text(
                "أرسل عدد الإحالات الجديد:",
                reply_markup=ReplyKeyboardRemove()
            )
            return ENTERING_NEW_REFERRAL_COUNT

        elif text == "تعديل الأرباح 💰":
            await update.message.reply_text(
                "أرسل المبلغ الجديد للأرباح:",
                reply_markup=ReplyKeyboardRemove()
            )
            return ENTERING_NEW_REFERRAL_EARNINGS

        return EDITING_USER_REFERRAL_DATA

    async def handle_entering_new_referral_count(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        text = update.message.text
        user_id = context.user_data.get('edit_referral_user_id')

        if not user_id:
            await update.message.reply_text("❌ حدث خطأ. يرجى المحاولة مرة أخرى")
            return await self.show_referral_management(update, context)

        try:
            new_count = int(text.strip())

            if new_count < 0:
                await update.message.reply_text("⚠️ العدد يجب أن يكون موجباً")
                return ENTERING_NEW_REFERRAL_COUNT

            await update.message.reply_text(
                f"⚠️ **تنبيه**: هذه الميزة لتعديل البيانات يدوياً فقط. لا تقوم بتحديث قائمة الإحالات الفعلية.\n\n"
                f"✅ تم حفظ العدد الجديد: {new_count}",
                parse_mode='Markdown'
            )

            context.user_data.pop('edit_referral_user_id', None)
            return await self.show_referral_management(update, context)

        except ValueError:
            await update.message.reply_text("⚠️ يرجى إدخال رقم صحيح")
            return ENTERING_NEW_REFERRAL_COUNT

    async def handle_entering_new_referral_earnings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        text = update.message.text
        user_id = context.user_data.get('edit_referral_user_id')

        if not user_id:
            await update.message.reply_text("❌ حدث خطأ. يرجى المحاولة مرة أخرى")
            return await self.show_referral_management(update, context)

        try:
            new_earnings = float(text.strip())

            if new_earnings < 0:
                await update.message.reply_text("⚠️ المبلغ يجب أن يكون موجباً")
                return ENTERING_NEW_REFERRAL_EARNINGS

            data_manager.edit_user_referrals(user_id, new_earnings=new_earnings)

            await update.message.reply_text(
                f"✅ تم تحديث الأرباح بنجاح!\n\nالأرباح الجديدة: **{new_earnings:,.2f} SYP**",
                parse_mode='Markdown'
            )

            context.user_data.pop('edit_referral_user_id', None)
            return await self.show_referral_management(update, context)

        except ValueError:
            await update.message.reply_text("⚠️ يرجى إدخال مبلغ صحيح")
            return ENTERING_NEW_REFERRAL_EARNINGS

# Initialize bot
bot = LodoxaBot()

async def main():
    """Main function to run the bot"""
    # Get bot token from environment variable
    bot_token = TELEGRAM_BOT_TOKEN
    if not bot_token:
        logger.critical("TELEGRAM_BOT_TOKEN is not set!")
        raise ValueError("TELEGRAM_BOT_TOKEN is required")

    # Verify admin ID is set
    if not ADMIN_ID:
        logger.critical("ADMIN_ID is not set! Admin notifications will not work.")
    else:
        logger.info(f"Admin ID set to: {ADMIN_ID}")

    # Log ADMG01C value
    if ADMG01C > 0:
        logger.info(f"ADMG01C set to: {ADMG01C}")
    else:
        logger.info("ADMG01C not configured (set to 0)")

    # Create application
    application = Application.builder().token(bot_token).build()

    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', bot.start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(bot.handle_subscription_check, pattern="^check_subscription$"),
                CallbackQueryHandler(bot.handle_show_my_statistics_callback, pattern="^show_my_statistics$"),
                CallbackQueryHandler(bot.handle_withdraw_referral_earnings, pattern="^withdraw_referral_earnings$"),
                CallbackQueryHandler(bot.handle_back_to_main_menu, pattern="^back_to_main_menu$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_main_menu)
            ],
            SELECTING_APP_GAME: [
                MessageHandler(filters.Regex("^شحن تطبيق 📱$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^شحن لعبة 🎮$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^شحن رصيد حسابك ➕$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^تواصل مع الدعم 💬$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^مدفوعات 🌟$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^لوحة التحكم 🛠$"), bot.handle_main_menu),
                CallbackQueryHandler(bot.handle_app_game_selection)
            ],
            SELECTING_CATEGORY: [
                MessageHandler(filters.Regex("^شحن تطبيق 📱$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^شحن لعبة 🎮$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^شحن رصيد حسابك ➕$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^تواصل مع الدعم 💬$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^مدفوعات 🌟$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^لوحة التحكم 🛠$"), bot.handle_main_menu),
                CallbackQueryHandler(bot.handle_category_selection)
            ],
            ENTERING_QUANTITY: [
                MessageHandler(filters.Regex("^شحن تطبيق 📱$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^شحن لعبة 🎮$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^شحن رصيد حسابك ➕$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^تواصل مع الدعم 💬$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^مدفوعات 🌟$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^لوحة التحكم 🛠$"), bot.handle_main_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_quantity_input_universal)
            ],
            ENTERING_ACCOUNT_ID: [
                MessageHandler(filters.Regex("^شحن تطبيق 📱$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^شحن لعبة 🎮$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^شحن رصيد حسابك ➕$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^تواصل مع الدعم 💬$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^مدفوعات 🌟$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^لوحة التحكم 🛠$"), bot.handle_main_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_account_id_input)
            ],
            CONFIRMING_ORDER: [CallbackQueryHandler(bot.handle_order_confirmation)],
            ADMIN_PANEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_admin_panel)],
            MANAGING_APPS: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_apps_management)],
            SUPPORT_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_support_message)],
            ADD_BALANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_add_balance)],
            SELECTING_APP_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_app_type_selection)],
            ENTERING_APP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_app_name_entry)],
            SELECTING_CATEGORY_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_category_service_selection)],
            SELECTING_CATEGORY_APP: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_category_app_selection)],
            SELECTING_CATEGORY_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_category_type_selection)],
            ENTERING_FIXED_CATEGORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_fixed_categories_entry)],
            ENTERING_QUANTITY_CATEGORY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_quantity_category_name)],
            ENTERING_MIN_ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_min_order_entry)],
            ENTERING_MAX_ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_max_order_entry)],
            ENTERING_PRICE_PER_UNIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_price_per_unit_entry)],
            SELECTING_DELETE_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_delete_action_selection)],
            SELECTING_DELETE_SERVICE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_delete_service_type_selection)],
            SELECTING_DELETE_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_delete_item_selection)],
            CONFIRMING_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_delete_confirmation)],
            CONFIRMING_DELETE_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_delete_category_confirmation)],
            SELECTING_DELETE_CATEGORY_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_delete_category_service_selection)],
            SELECTING_DELETE_CATEGORY_APP: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_delete_category_app_selection)],
            SELECTING_DELETE_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_delete_category_selection)],
            SETTING_SUPPORT_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_support_username_setting)],
            SELECTING_PAYMENT_METHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_payment_method_selection)],
            SELECTING_SHAMCASH_CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_shamcash_currency_selection)],
            ENTERING_CHARGE_CODE: [
                MessageHandler(filters.Regex("^شحن تطبيق 📱$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^شحن لعبة 🎮$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^شحن رصيد حسابك ➕$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^تواصل مع الدعم 💬$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^مدفوعات 🌟$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^لوحة التحكم 🛠$"), bot.handle_main_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_charge_code_input)
            ],
            ENTERING_SYRIATEL_TRANSACTION: [
                MessageHandler(filters.Regex("^شحن تطبيق 📱$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^شحن لعبة 🎮$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^شحن رصيد حسابك ➕$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^تواصل مع الدعم 💬$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^مدفوعات 🌟$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^لوحة التحكم 🛠$"), bot.handle_main_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_syriatel_transaction_input)
            ],
            ENTERING_SYRIATEL_AMOUNT: [
                MessageHandler(filters.Regex("^شحن تطبيق 📱$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^شحن لعبة 🎮$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^شحن رصيد حسابك ➕$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^تواصل مع الدعم 💬$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^مدفوعات 🌟$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^لوحة التحكم 🛠$"), bot.handle_main_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_syriatel_amount_input)
            ],
            CONFIRMING_SYRIATEL_PAYMENT: [CallbackQueryHandler(bot.handle_syriatel_payment_confirmation)],
            MANAGING_PAYMENT_ADDRESSES: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_payment_addresses_management)],
            SETTING_SYRIATEL_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_syriatel_address_setting)],
            SETTING_SHAMCASH_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_shamcash_address_setting)],
            SETTING_PAYEER_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_payeer_data_setting)],
            SETTING_USDT_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_usdt_data_setting)],
            MANAGING_CHARGE_CODES: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_charge_codes_management)],
            ENTERING_CHARGE_CODE_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_charge_code_value_entry)],
            CONFIRMING_CHARGE_CODE_GENERATION: [CallbackQueryHandler(bot.handle_charge_code_generation_confirmation)],
            MANAGING_PAYMENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_payments_management)],
            ENTERING_PAYMENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_payment_name_entry)],
            ENTERING_PAYMENT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_payment_price_entry)],
            CONFIRMING_PAYMENT_ADD: [CallbackQueryHandler(bot.handle_payment_add_confirmation)],
            SELECTING_PAYMENT_TO_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_payment_deletion_selection)],
            CONFIRMING_PAYMENT_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_payment_delete_confirmation)],
            ENTERING_BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_broadcast_message_entry)],
            CONFIRMING_BROADCAST: [CallbackQueryHandler(bot.handle_broadcast_confirmation)],
            BOT_SETTINGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_bot_settings)],
            MANAGING_PAYMENT_SERVICES: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_payments_management)],
            ENTERING_SERVICE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_service_name_entry)],
            ENTERING_CATEGORY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_category_name_entry)],
            ENTERING_CATEGORY_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_category_price_entry)],
            SELECTING_CATEGORY_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_category_type_selection)],

            CONFIRMING_CATEGORY_ADD: [CallbackQueryHandler(bot.handle_category_add_confirmation)],
            SELECTING_SERVICE_TO_EDIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_service_selection_for_edit)],
            ADDING_SERVICE_CATEGORIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_service_categories_management)],
            ENTERING_PAYMENT_INPUT_DATA: [
                MessageHandler(filters.Regex("^شحن تطبيق 📱$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^شحن لعبة 🎮$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^شحن رصيد حسابك ➕$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^تواصل مع الدعم 💬$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^مدفوعات 🌟$"), bot.handle_main_menu),
                MessageHandler(filters.Regex("^لوحة التحكم 🛠$"), bot.handle_main_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_payment_input_data)
            ],
            CONFIRMING_PAYMENT_SERVICE_ORDER: [CallbackQueryHandler(bot.handle_payment_service_order_confirmation)],
            SELECTING_CATEGORY_TO_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_category_delete_selection)],
            CONFIRMING_CATEGORY_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_category_delete_confirmation)],
            SELECTING_CATEGORY_TO_EDIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_category_edit_selection)],
            EDITING_CATEGORY_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_category_price_edit)],
            CONFIRMING_CATEGORY_EDIT: [CallbackQueryHandler(bot.handle_category_edit_confirmation)],
            USER_MANAGEMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_user_management)],
            VIEWING_STATISTICS: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_statistics_menu)],
            ENTERING_USER_ID_FOR_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_user_id_input)],
            SELECTING_USER_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_user_management)],
            CONFIRMING_USER_ACTION: [CallbackQueryHandler(bot.handle_user_action_callbacks)],
            ENTERING_FREEZE_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_freeze_duration_input)],
            ENTERING_BALANCE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_balance_amount_input)],
            ENTERING_PRIVATE_MESSAGE_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_private_message_user_id)],
            ENTERING_PRIVATE_MESSAGE_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_private_message_text)],
            CONFIRMING_PRIVATE_MESSAGE: [CallbackQueryHandler(bot.handle_user_action_callbacks)],
            MANAGING_AGENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_agents_management)],
            ENTERING_AGENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_agent_name_entry)],
            ENTERING_AGENT_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_agent_user_id_entry)],
            ENTERING_AGENT_COMMISSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_agent_commission_entry)],
            CONFIRMING_AGENT_ADD: [CallbackQueryHandler(bot.handle_agent_add_confirmation)],
            SELECTING_AGENT_TO_EDIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_agent_selection)],
            EDITING_AGENT_COMMISSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_agent_commission_edit)],
            CONFIRMING_AGENT_EDIT: [CallbackQueryHandler(bot.handle_agent_callbacks)],
            CONFIRMING_AGENT_DELETE: [CallbackQueryHandler(bot.handle_agent_callbacks)],
            SETTING_WITHDRAWAL_FEES: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_withdrawal_fees_setting)],
            AGENT_PANEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_agent_panel)],
            CONFIRMING_WITHDRAWAL_REQUEST: [CallbackQueryHandler(bot.handle_withdrawal_confirmation)],
            BULK_PRICE_ADJUSTMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_bulk_price_adjustment)],
            ENTERING_ADJUSTMENT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_adjustment_value_entry)],
            CONFIRMING_BULK_ADJUSTMENT: [CallbackQueryHandler(bot.handle_bulk_adjustment_confirmation)],
            MANAGING_ORDERS_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_orders_channel_settings)],
            ADMG01C_PANEL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_admg01c_panel),
                CallbackQueryHandler(bot.handle_admin_callbacks_admg01c, pattern=r"^(confirm_admins_warning|cancel_admins_warning)$")
            ],
            ENTERING_NEW_BOT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_new_bot_name_entry)],
            CONFIRMING_BOT_NAME_CHANGE: [CallbackQueryHandler(bot.handle_bot_name_change_confirmation)],
            MANAGING_ADMINS_ADMG01C: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_admins_management_admg01c)],
            ADDING_ADMIN_ADMG01C: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_admin_name_entry_admg01c)],
            ENTERING_ADMIN_USER_ID_ADMG01C: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_admin_user_id_entry_admg01c)],
            CONFIRMING_ADMIN_ADD_ADMG01C: [CallbackQueryHandler(bot.handle_admin_callbacks_admg01c)],
            SELECTING_ADMIN_TO_DELETE_ADMG01C: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_admin_selection_for_delete_admg01c)],
            CONFIRMING_ADMIN_DELETE_ADMG01C: [CallbackQueryHandler(bot.handle_admin_callbacks_admg01c)],
            MANAGING_ADMINS: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_admins_management)],
            ENTERING_ADMIN_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_admin_user_id_entry)],
            ADDING_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_admin_name_entry)],
            CONFIRMING_ADMIN_ADD: [CallbackQueryHandler(bot.handle_admin_callbacks)],
            SELECTING_ADMIN_TO_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_admin_selection_for_delete)],
            CONFIRMING_ADMIN_DELETE: [CallbackQueryHandler(bot.handle_admin_callbacks)],
            MANAGING_REFERRALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_referral_management)],
            VIEWING_TOP_REFERRERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_viewing_top_referrers)],
            VIEWING_REFERRAL_TRANSACTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_viewing_referral_transactions)],
            ENTERING_REFERRAL_RATES: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_entering_referral_rates)],
            ENTERING_REFERRAL_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_entering_referral_user_id)],
            EDITING_USER_REFERRAL_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_editing_user_referral_data)],
            ENTERING_NEW_REFERRAL_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_entering_new_referral_count)],
            ENTERING_NEW_REFERRAL_EARNINGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_entering_new_referral_earnings)],
        },
        fallbacks=[CommandHandler('start', bot.start)],
        allow_reentry=True
    )

    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(bot.handle_subscription_check, pattern="^check_subscription$"))
    application.add_handler(CallbackQueryHandler(bot.handle_admin_order_action, pattern=r"^(approve|reject)_order_"))
    application.add_handler(CallbackQueryHandler(bot.handle_admin_charge_action, pattern=r"^(approve|reject)_transfer_"))
    application.add_handler(CallbackQueryHandler(bot.handle_payment_service_selection, pattern=r"^payment_service_"))
    application.add_handler(CallbackQueryHandler(bot.handle_payment_category_selection, pattern=r"^payment_category_"))
    application.add_handler(CallbackQueryHandler(bot.handle_payment_service_selection, pattern="^back_to_main$"))
    application.add_handler(CallbackQueryHandler(bot.handle_payment_service_selection, pattern="^back_to_payments$"))
    application.add_handler(CallbackQueryHandler(bot.handle_admin_payment_order_action, pattern=r"^(complete|reject)_payment_order_"))
    application.add_handler(CallbackQueryHandler(bot.handle_user_action_callbacks, pattern=r"^(confirm_action_|confirm_freeze_|send_private_message_|cancel_|close_)"))
    application.add_handler(CallbackQueryHandler(bot.handle_agent_callbacks, pattern=r"^(confirm_add_agent|cancel_add_agent|confirm_delete_agent_|confirm_edit_agent_|cancel_agent_action)"))
    application.add_handler(CallbackQueryHandler(bot.handle_withdrawal_confirmation, pattern=r"^(confirm_withdrawal|cancel_withdrawal)"))
    application.add_handler(CallbackQueryHandler(bot.handle_bulk_adjustment_confirmation, pattern=r"^(confirm_bulk_adjustment|cancel_bulk_adjustment)"))
    application.add_handler(CallbackQueryHandler(bot.handle_admin_callbacks_admg01c, pattern=r"^(confirm_add_admin_|cancel_add_admin_admg01c|confirm_delete_admin_|cancel_delete_admin_admg01c)"))
    application.add_handler(CallbackQueryHandler(bot.handle_admin_callbacks, pattern=r"^(confirm_add_admin_|cancel_add_admin|confirm_delete_admin_|cancel_delete_admin)"))

    # Referral system command handlers
    application.add_handler(CommandHandler('referral_toggle', bot.handle_referral_toggle))
    application.add_handler(CommandHandler('referral_rates', bot.handle_referral_rates))

    logger.info("Bot is starting...")

    # Run the bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    try:
        # Keep the bot running
        import signal
        import asyncio

        stop_event = asyncio.Event()

        def signal_handler(signum, frame):
            logger.info("Received signal to stop bot")
            stop_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        await stop_event.wait()
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())