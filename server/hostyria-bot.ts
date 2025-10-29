import TelegramBot from 'node-telegram-bot-api';
import { db } from './db';
import { users, repositories } from '@shared/schema';
import { eq } from 'drizzle-orm';
import bcrypt from 'bcrypt';

const BOT_TOKEN = process.env.HOSTYRIA_BOT_TOKEN;

if (!BOT_TOKEN) {
  console.error('HOSTYRIA_BOT_TOKEN environment variable is not set');
  process.exit(1);
}

const bot = new TelegramBot(BOT_TOKEN, { polling: true });

// Store user sessions (telegram_id -> user data)
const userSessions = new Map<number, { userId: string; email: string; username: string }>();
const loginStates = new Map<number, { step: 'email' | 'password'; email?: string }>();

// Welcome message with login
function sendWelcomeMessage(chatId: number) {
  const welcomeText = `Welcome 🤗\nYou are not logged in yet.`;

  const keyboard = {
    inline_keyboard: [
      [{ text: 'Login 🔗', callback_data: 'login' }],
      [{ text: 'Support 🆘', callback_data: 'support' }]
    ]
  };

  bot.sendMessage(chatId, welcomeText, { reply_markup: keyboard });
}

// Support message
function sendSupportMessage(chatId: number) {
  const supportText = `You can contact us with:\n\nTelegram support bot:\n@TurboTel\n\nEmail: HostYria.Team@TurboTel.com`;

  bot.sendMessage(chatId, supportText);
}

// Main dashboard
async function sendDashboard(chatId: number) {
  const session = userSessions.get(chatId);

  if (!session) {
    sendWelcomeMessage(chatId);
    return;
  }

  const [user] = await db.select().from(users).where(eq(users.id, session.userId)).limit(1);

  if (!user) {
    userSessions.delete(chatId);
    sendWelcomeMessage(chatId);
    return;
  }

  const balance = parseFloat(user.balance || '0');
  const dashboardText = `Welcome ${session.username} in HostYria manager:\n\nYour Email: ${session.email}\nBalance: $${balance.toFixed(2)}`;

  const keyboard = {
    inline_keyboard: [
      [{ text: 'My Repository', callback_data: 'my_repository' }],
      [{ text: 'Support 🆘', callback_data: 'support' }],
      [{ text: 'Sign out', callback_data: 'logout' }]
    ]
  };

  bot.sendMessage(chatId, dashboardText, { reply_markup: keyboard });
}

// Show repositories
async function showRepositories(chatId: number) {
  const session = userSessions.get(chatId);

  if (!session) {
    sendWelcomeMessage(chatId);
    return;
  }

  const userRepos = await db.select().from(repositories).where(eq(repositories.userId, session.userId));

  if (userRepos.length === 0) {
    bot.sendMessage(chatId, 'You have no repositories yet.');
    return;
  }

  const keyboard = {
    inline_keyboard: userRepos.map(repo => [
      { text: `${repo.name} (${repo.status})`, callback_data: `repo_${repo.id}` }
    ]).concat([[{ text: '← Back', callback_data: 'back_to_dashboard' }]])
  };

  bot.sendMessage(chatId, 'Your Repositories:', { reply_markup: keyboard });
}

// Show repository details
async function showRepositoryDetails(chatId: number, repoId: string) {
  const session = userSessions.get(chatId);

  if (!session) {
    sendWelcomeMessage(chatId);
    return;
  }

  const [repo] = await db.select().from(repositories)
    .where(eq(repositories.id, repoId))
    .limit(1);

  if (!repo || repo.userId !== session.userId) {
    bot.sendMessage(chatId, 'Repository not found.');
    return;
  }

  const repoText = `Repo name: ${repo.name}\nStatus: ${repo.status}`;

  const actionButton = repo.status === 'running' 
    ? { text: 'Stop', callback_data: `stop_${repoId}` }
    : { text: 'Start', callback_data: `start_${repoId}` };

  const keyboard = {
    inline_keyboard: [
      [actionButton],
      [{ text: '← Back to Repositories', callback_data: 'my_repository' }]
    ]
  };

  bot.sendMessage(chatId, repoText, { reply_markup: keyboard });
}

// Handle /start command
bot.onText(/\/start/, async (msg) => {
      const chatId = msg.chat.id;
      const telegramUsername = msg.from?.username || '';

      const user = await db.select().from(users).where(eq(users.telegramUsername, telegramUsername)).limit(1);

      if (user.length === 0) {
        bot.sendMessage(chatId, 
          'Welcome to HostYria! 🚀\n\n' +
          'Please register first using our website and link your Telegram username in your account settings.'
        );
      } else {
        const userBalance = parseFloat(user[0].balance || '0');
        bot.sendMessage(
          chatId,
          `Welcome back, ${user[0].username}! 👋\n\n` +
          `Your current balance: $${userBalance.toFixed(2)}\n\n` +
          'What would you like to do?',
          {
            reply_markup: {
              keyboard: [
                ['📊 Check Balance', '📂 My Repositories'],
                ['💬 Support'],
                ['🚪 Sign out']
              ],
              resize_keyboard: true
            }
          }
        );
      }
    });

// Handle callback queries
bot.on('callback_query', async (query) => {
  const chatId = query.message!.chat.id;
  const data = query.data!;

  await bot.answerCallbackQuery(query.id);

  if (data === 'login') {
    loginStates.set(chatId, { step: 'email' });
    bot.sendMessage(chatId, 'Enter your HostYria email:');
  } else if (data === 'support') {
    sendSupportMessage(chatId);
  } else if (data === 'my_repository') {
    await showRepositories(chatId);
  } else if (data === 'back_to_dashboard') {
    await sendDashboard(chatId);
  } else if (data === 'logout') {
    userSessions.delete(chatId);
    loginStates.delete(chatId);
    bot.sendMessage(chatId, 'You have been logged out successfully.');
    sendWelcomeMessage(chatId);
  } else if (data.startsWith('repo_')) {
    const repoId = data.substring(5);
    await showRepositoryDetails(chatId, repoId);
  } else if (data.startsWith('start_') || data.startsWith('stop_')) {
    const action = data.startsWith('start_') ? 'start' : 'stop';
    const repoId = data.substring(action.length + 1);

    const session = userSessions.get(chatId);
    if (!session) {
      sendWelcomeMessage(chatId);
      return;
    }

    const [repo] = await db.select().from(repositories)
      .where(eq(repositories.id, repoId))
      .limit(1);

    if (!repo || repo.userId !== session.userId) {
      bot.sendMessage(chatId, 'Repository not found.');
      return;
    }

    const newStatus = action === 'start' ? 'running' : 'stopped';
    await db.update(repositories)
      .set({ status: newStatus })
      .where(eq(repositories.id, repoId));

    bot.sendMessage(chatId, `Repository ${action === 'start' ? 'started' : 'stopped'} successfully!`);
    await showRepositoryDetails(chatId, repoId);
  }
});

// Handle text messages (for login flow)
bot.on('message', async (msg) => {
  const chatId = msg.chat.id;
  const text = msg.text;

  if (!text || text.startsWith('/')) return;

  const loginState = loginStates.get(chatId);

  if (!loginState) return;

  if (loginState.step === 'email') {
    loginState.email = text;
    loginState.step = 'password';
    loginStates.set(chatId, loginState);
    bot.sendMessage(chatId, 'Enter your HostYria password:');
  } else if (loginState.step === 'password') {
    const email = loginState.email!;
    const password = text;

    bot.sendMessage(chatId, 'Animation login... ⏳');

    // Authenticate user
    const [user] = await db.select().from(users).where(eq(users.email, email)).limit(1);

    if (!user) {
      loginStates.delete(chatId);
      bot.sendMessage(chatId, 'Login failed, please check your login information.\n\nOr you can contact us (press Support 🆘) for more details.');
      sendWelcomeMessage(chatId);
      return;
    }

    const passwordMatch = await bcrypt.compare(password, user.password);

    if (!passwordMatch) {
      loginStates.delete(chatId);
      bot.sendMessage(chatId, 'Login failed, please check your login information.\n\nOr you can contact us (press Support 🆘) for more details.');
      sendWelcomeMessage(chatId);
      return;
    }

    // Login successful
    userSessions.set(chatId, {
      userId: user.id,
      email: user.email,
      username: user.username
    });
    loginStates.delete(chatId);

    await sendDashboard(chatId);
  }
});

bot.onText(/🚪 Sign out/, async (msg) => {
      const chatId = msg.chat.id;

      bot.sendMessage(
        chatId,
        'You have been signed out. Use /start to sign in again.',
        {
          reply_markup: {
            remove_keyboard: true
          }
        }
      );
    });

console.log('HostYria Bot started successfully! 🚀');

export default bot;