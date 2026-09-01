import { randomUUID } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import express, { type Request, type Response } from "express";

type Transaction = {
  id: string;
  description: string;
  amount: number;
  kind: "income" | "expense";
  date: string;
};

const port = Number(process.env.PORT || 3000);
const aiCoreUrl = (process.env.PYTHON_API_URL || "http://127.0.0.1:8001").replace(/\/$/, "");
const dataFile = path.resolve(process.env.FINWISE_DATA_FILE || "data/transactions.json");

const app = express();
app.use(express.json({ limit: "100kb" }));
app.use((_request, response, next) => {
  response.setHeader("Access-Control-Allow-Origin", process.env.CLIENT_URL || "http://localhost:5173");
  response.setHeader("Access-Control-Allow-Headers", "Content-Type");
  response.setHeader("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS");
  next();
});
app.options("/{*path}", (_request, response) => response.sendStatus(204));

const loadTransactions = async (): Promise<Transaction[]> => {
  try {
    const raw = await readFile(dataFile, "utf8");
    const parsed: unknown = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed as Transaction[] : [];
  } catch (error: any) {
    if (error?.code === "ENOENT") return [];
    throw error;
  }
};

const saveTransactions = async (transactions: Transaction[]) => {
  await mkdir(path.dirname(dataFile), { recursive: true });
  await writeFile(dataFile, `${JSON.stringify(transactions, null, 2)}\n`, "utf8");
};

const summaryFor = (transactions: Transaction[]) => {
  const income = transactions.filter(item => item.kind === "income").reduce((total, item) => total + item.amount, 0);
  const expenses = transactions.filter(item => item.kind === "expense").reduce((total, item) => total + item.amount, 0);
  return { income, expenses, balance: income - expenses, transactionCount: transactions.length };
};

const isTransactionInput = (value: unknown): value is Omit<Transaction, "id"> => {
  if (!value || typeof value !== "object") return false;
  const input = value as Record<string, unknown>;
  return typeof input.description === "string" && input.description.trim().length > 0 &&
    typeof input.amount === "number" && Number.isFinite(input.amount) && input.amount > 0 &&
    (input.kind === "income" || input.kind === "expense") && typeof input.date === "string";
};

app.get("/health", async (_request, response) => {
  response.json({ ok: true, service: "finwise-simple-api", storage: dataFile, aiCoreUrl });
});

app.get("/api/transactions", async (_request, response) => {
  const transactions = await loadTransactions();
  response.json({ transactions: transactions.sort((a, b) => b.date.localeCompare(a.date)), summary: summaryFor(transactions) });
});

app.post("/api/transactions", async (request, response) => {
  if (!isTransactionInput(request.body)) {
    response.status(400).json({ error: "Provide description, a positive numeric amount, kind (income or expense), and date." });
    return;
  }
  const transactions = await loadTransactions();
  const transaction: Transaction = { ...request.body, id: randomUUID(), description: request.body.description.trim() };
  transactions.push(transaction);
  await saveTransactions(transactions);
  response.status(201).json({ transaction, summary: summaryFor(transactions) });
});

app.delete("/api/transactions/:id", async (request, response) => {
  const transactions = await loadTransactions();
  const remaining = transactions.filter(item => item.id !== request.params.id);
  if (remaining.length === transactions.length) {
    response.status(404).json({ error: "Transaction not found." });
    return;
  }
  await saveTransactions(remaining);
  response.json({ summary: summaryFor(remaining) });
});

app.post("/api/ai/analyze", async (request: Request, response: Response) => {
  const question = typeof request.body?.question === "string" ? request.body.question.trim() : "";
  if (!question) {
    response.status(400).json({ error: "Ask the financial copilot a question." });
    return;
  }
  const transactions = await loadTransactions();
  const summary = summaryFor(transactions);
  const userProfile = {
    annual_income: summary.income * 12,
    monthly_expenses: summary.expenses,
    savings: Math.max(summary.balance, 0),
    debts: [], financial_goals: [], risk_tolerance: "moderate", investment_experience: "beginner", time_horizon: 10,
    transactions,
  };
  try {
    const aiResponse = await fetch(`${aiCoreUrl}/api/agents/process`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_input: question, user_profile: userProfile, options: { narrative: true } }),
      signal: AbortSignal.timeout(45_000),
    });
    const data: unknown = await aiResponse.json();
    if (!aiResponse.ok) throw new Error(`AI Core returned ${aiResponse.status}`);
    response.json(data);
  } catch (error) {
    response.status(503).json({
      error: "The LangGraph AI Core is unavailable. Start it on port 8001 and configure a provider key for live narratives.",
      detail: error instanceof Error ? error.message : "Unknown AI Core error",
    });
  }
});

app.use((error: unknown, _request: Request, response: Response, _next: unknown) => {
  console.error(error);
  response.status(500).json({ error: "The API could not complete that request." });
});

app.listen(port, () => console.log(`FinWise simple API listening on http://localhost:${port}`));
