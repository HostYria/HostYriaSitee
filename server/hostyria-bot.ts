import TelegramBot from 'node-telegram-bot-api';
import { db } from './db';
import { users, repositories } from '@shared/schema';
import { eq, isNotNull } from 'drizzle-orm';
import bcrypt from 'bcrypt';
import { pythonProcessManager } from './pythonProcessManager';

const BOT_TOKEN = process.env.HOSTYRIA_BOT_TOKEN;
const ENABLE_BOT = process.env.ENABLE_TELEGRAM_BOT !== 'false';

if (!BOT_TOKEN) {
  console.error('HOSTYRIA_BOT_TOKEN environment variable is not set');
  process.exit(1);
}

const bot = new TelegramBot(BOT_TOKEN, { polling: ENABLE_BOT });

if (!ENABLE_BOT) {
  console.log('⚠️  Telegram Bot polling is DISABLED (ENABLE_TELEGRAM_BOT=false)');
  console.log('   The bot will not respond to messages until enabled.');
}

// Store user sessions (telegram_id -> user data)
const userSessions = new Map<number, { userId: string; email: string; username: string }>();
const loginStates = new Map<number, { step: 'email' | 'password'; email?: string }>();
const messageIds = new Map<number, number>(); // Store last message ID for each chat

// Load sessions from database on startup
async function loadSessionsFromDatabase() {
  try {
    const usersWithTelegram = await db.select().from(users).where(isNotNull(users.telegramChatId));
    for (const user of usersWithTelegram) {
      if (user.telegramChatId) {
        const chatId = parseInt(user.telegramChatId);
        userSessions.set(chatId, {
          userId: user.id,
          email: user.email,
          username: user.username
        });
      }
    }
    console.log(`Loaded ${userSessions.size} Telegram sessions from database`);
  } catch (error) {
    console.error('Error loading Telegram sessions:', error);
  }
}

// Call on startup only if bot is enabled
if (ENABLE_BOT) {
  loadSessionsFromDatabase();
}

// Welcome message with login
async function sendWelcomeMessage(chatId: number) {
  const welcomeText = `Welcome 🤗\nYou are not logged in yet.`;

  const keyboard = {
    inline_keyboard: [
      [{ text: 'Login 🔗', callback_data: 'login' }],
      [{ text: 'Support 🆘', callback_data: 'support' }]
    ]
  };

  const lastMessageId = messageIds.get(chatId);

  try {
    if (lastMessageId) {
      await bot.editMessageText(welcomeText, {
        chat_id: chatId,
        message_id: lastMessageId,
        reply_markup: keyboard
      });
    } else {
      const sent = await bot.sendMessage(chatId, welcomeText, { reply_markup: keyboard });
      messageIds.set(chatId, sent.message_id);
    }
  } catch (error) {
    // If edit fails, send new message
    const sent = await bot.sendMessage(chatId, welcomeText, { reply_markup: keyboard });
    messageIds.set(chatId, sent.message_id);
  }
}

// Support message
async function sendSupportMessage(chatId: number) {
  const supportText = `You can contact us with:\n\nTelegram support bot:\n@HostYria_Support_Bot\n\nEmail: HostYria.Team@gmail.com`;

  const lastMessageId = messageIds.get(chatId);

  try {
    if (lastMessageId) {
      await bot.editMessageText(supportText, {
        chat_id: chatId,
        message_id: lastMessageId
      });
    } else {
      const sent = await bot.sendMessage(chatId, supportText);
      messageIds.set(chatId, sent.message_id);
    }
  } catch (error) {
    const sent = await bot.sendMessage(chatId, supportText);
    messageIds.set(chatId, sent.message_id);
  }
}

// Main dashboard
async function sendDashboard(chatId: number) {
  const session = userSessions.get(chatId);

  if (!session) {
    await sendWelcomeMessage(chatId);
    return;
  }

  const [user] = await db.select().from(users).where(eq(users.id, session.userId)).limit(1);

  if (!user) {
    userSessions.delete(chatId);
    await sendWelcomeMessage(chatId);
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

  const lastMessageId = messageIds.get(chatId);

  try {
    if (lastMessageId) {
      await bot.editMessageText(dashboardText, {
        chat_id: chatId,
        message_id: lastMessageId,
        reply_markup: keyboard
      });
    } else {
      const sent = await bot.sendMessage(chatId, dashboardText, { reply_markup: keyboard });
      messageIds.set(chatId, sent.message_id);
    }
  } catch (error) {
    const sent = await bot.sendMessage(chatId, dashboardText, { reply_markup: keyboard });
    messageIds.set(chatId, sent.message_id);
  }
}

// Show repositories
async function showRepositories(chatId: number) {
  const session = userSessions.get(chatId);

  if (!session) {
    await sendWelcomeMessage(chatId);
    return;
  }

  const userRepos = await db.select().from(repositories).where(eq(repositories.userId, session.userId));

  if (userRepos.length === 0) {
    const lastMessageId = messageIds.get(chatId);
    const text = 'You have no repositories yet.';

    try {
      if (lastMessageId) {
        await bot.editMessageText(text, {
          chat_id: chatId,
          message_id: lastMessageId
        });
      } else {
        const sent = await bot.sendMessage(chatId, text);
        messageIds.set(chatId, sent.message_id);
      }
    } catch (error) {
      const sent = await bot.sendMessage(chatId, text);
      messageIds.set(chatId, sent.message_id);
    }
    return;
  }

  const keyboard = {
    inline_keyboard: userRepos.map(repo => [
      { text: `${repo.name} (${repo.status})`, callback_data: `repo_${repo.id}` }
    ]).concat([[{ text: '← Back', callback_data: 'back_to_dashboard' }]])
  };

  const lastMessageId = messageIds.get(chatId);

  try {
    if (lastMessageId) {
      await bot.editMessageText('Your Repositories:', {
        chat_id: chatId,
        message_id: lastMessageId,
        reply_markup: keyboard
      });
    } else {
      const sent = await bot.sendMessage(chatId, 'Your Repositories:', { reply_markup: keyboard });
      messageIds.set(chatId, sent.message_id);
    }
  } catch (error) {
    const sent = await bot.sendMessage(chatId, 'Your Repositories:', { reply_markup: keyboard });
    messageIds.set(chatId, sent.message_id);
  }
}

// Show repository details
async function showRepositoryDetails(chatId: number, repoId: string) {
  const session = userSessions.get(chatId);

  if (!session) {
    await sendWelcomeMessage(chatId);
    return;
  }

  const [repo] = await db.select().from(repositories)
    .where(eq(repositories.id, repoId))
    .limit(1);

  if (!repo || repo.userId !== session.userId) {
    const lastMessageId = messageIds.get(chatId);
    const text = 'Repository not found.';

    try {
      if (lastMessageId) {
        await bot.editMessageText(text, {
          chat_id: chatId,
          message_id: lastMessageId
        });
      } else {
        const sent = await bot.sendMessage(chatId, text);
        messageIds.set(chatId, sent.message_id);
      }
    } catch (error) {
      const sent = await bot.sendMessage(chatId, text);
      messageIds.set(chatId, sent.message_id);
    }
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

  const lastMessageId = messageIds.get(chatId);

  try {
    if (lastMessageId) {
      await bot.editMessageText(repoText, {
        chat_id: chatId,
        message_id: lastMessageId,
        reply_markup: keyboard
      });
    } else {
      const sent = await bot.sendMessage(chatId, repoText, { reply_markup: keyboard });
      messageIds.set(chatId, sent.message_id);
    }
  } catch (error) {
    const sent = await bot.sendMessage(chatId, repoText, { reply_markup: keyboard });
    messageIds.set(chatId, sent.message_id);
  }
}

// Handle /start command
bot.onText(/\/start/, async (msg) => {
  const chatId = msg.chat.id;
  messageIds.set(chatId, msg.message_id);

  if (userSessions.has(chatId)) {
    await sendDashboard(chatId);
  } else {
    await sendWelcomeMessage(chatId);
  }
});

// Handle callback queries
bot.on('callback_query', async (query) => {
  const chatId = query.message!.chat.id;
  const data = query.data!;

  await bot.answerCallbackQuery(query.id);

  // Store the message ID from callback query
  if (query.message) {
    messageIds.set(chatId, query.message.message_id);
  }

  if (data === 'login') {
    loginStates.set(chatId, { step: 'email' });
    try {
      await bot.editMessageText('Enter your HostYria email:', {
        chat_id: chatId,
        message_id: query.message!.message_id
      });
    } catch (error) {
      const sent = await bot.sendMessage(chatId, 'Enter your HostYria email:');
      messageIds.set(chatId, sent.message_id);
    }
  } else if (data === 'support') {
    await sendSupportMessage(chatId);
  } else if (data === 'my_repository') {
    await showRepositories(chatId);
  } else if (data === 'back_to_dashboard') {
    await sendDashboard(chatId);
  } else if (data === 'logout') {
    const session = userSessions.get(chatId);
    if (session) {
      // Remove telegramChatId from database
      await db.update(users)
        .set({ telegramChatId: null })
        .where(eq(users.id, session.userId));
    }
    userSessions.delete(chatId);
    loginStates.delete(chatId);

    try {
      await bot.editMessageText('You have been logged out successfully.', {
        chat_id: chatId,
        message_id: query.message!.message_id
      });
    } catch (error) {
      await bot.sendMessage(chatId, 'You have been logged out successfully.');
    }

    await sendWelcomeMessage(chatId);
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

    try {
      if (action === 'start') {
        bot.sendMessage(chatId, '⏳ Starting repository...');
        await pythonProcessManager.startRepository(repoId);
        bot.sendMessage(chatId, '✅ Repository started successfully!');
      } else {
        bot.sendMessage(chatId, '⏳ Stopping repository...');
        if (pythonProcessManager.isRunning(repoId)) {
          pythonProcessManager.stopRepository(repoId);
        } else {
          await db.update(repositories)
            .set({ status: 'stopped' })
            .where(eq(repositories.id, repoId));
        }
        bot.sendMessage(chatId, '⏹️ Repository stopped successfully!');
      }
      await showRepositoryDetails(chatId, repoId);
    } catch (error: any) {
      bot.sendMessage(chatId, `❌ Error: ${error.message || 'Failed to ' + action + ' repository'}`);
    }
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

    // Login successful - save session in memory and database
    userSessions.set(chatId, {
      userId: user.id,
      email: user.email,
      username: user.username
    });
    loginStates.delete(chatId);

    // Save telegramChatId to database
    await db.update(users)
      .set({ telegramChatId: chatId.toString() })
      .where(eq(users.id, user.id));

    await sendDashboard(chatId);
  }
});

if (ENABLE_BOT) {
  console.log('HostYria Bot started successfully! 🚀');
} else {
  console.log('HostYria Bot initialized (polling disabled)');
}

export default bot;