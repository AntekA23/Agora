export interface InvoiceItem {
  name: string;
  quantity: number;
  price: number;
}

export interface InvoiceTaskInput {
  client_name: string;
  client_address: string;
  items: InvoiceItem[];
  notes: string;
}

export interface CashflowItem {
  description: string;
  amount: number;
  date?: string;
  category?: string;
}

export interface CashflowTaskInput {
  income: CashflowItem[];
  expenses: CashflowItem[];
  period: string;
}
