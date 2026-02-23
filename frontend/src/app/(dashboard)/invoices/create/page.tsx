"use client";

import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { useToast } from "@/components/ui/use-toast";

const invoiceFormSchema = z.object({
  customer_id: z.string().min(3, "Customer ID must be at least 3 characters"),
  total: z.number().positive("Total must be a positive number"),
  currency: z.string().min(1).max(3, "Currency must be at most 3 characters"),
});

type InvoiceFormValues = z.infer<typeof invoiceFormSchema>;

async function submitInvoice(formData: InvoiceFormValues): Promise<Response> {
  const payload = {
    source: "web_form",
    invoices: [
      {
        external_id: "WEB-" + crypto.randomUUID(),
        customer_id: formData.customer_id,
        issued_at: new Date().toISOString(),
        total: formData.total,
        currency: formData.currency,
      },
    ],
  };

  const response = await fetch("http://localhost:8080/api/v1/invoice-batches", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Ingest-Key": "local-dev-ingest-key",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message ?? `Request failed with status ${response.status}`);
  }

  return response;
}

export default function CreateInvoicePage() {
  const { toast } = useToast();

  const form = useForm<InvoiceFormValues>({
    resolver: zodResolver(invoiceFormSchema),
    defaultValues: {
      customer_id: "",
      total: 0,
      currency: "COP",
    },
  });

  const mutation = useMutation({
    mutationFn: submitInvoice,
    onSuccess: () => {
      toast({
        title: "Invoice sent to processing queue",
        description: "Your invoice has been submitted successfully.",
      });
      form.reset();
    },
    onError: (error: Error) => {
      toast({
        variant: "destructive",
        title: "Error submitting invoice",
        description: error.message,
      });
    },
  });

  function onSubmit(values: InvoiceFormValues) {
    mutation.mutate(values);
  }

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Create Invoice</CardTitle>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <FormField
                control={form.control}
                name="customer_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Customer ID</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g. CUST-001" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="total"
                render={({ field: { onChange, value, ...field } }) => (
                  <FormItem>
                    <FormLabel>Total</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        placeholder="e.g. 150000"
                        value={value === 0 ? "" : value}
                        onChange={(e) => onChange(isNaN(e.target.valueAsNumber) ? 0 : e.target.valueAsNumber)}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="currency"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Currency</FormLabel>
                    <FormControl>
                      <Input placeholder="COP" maxLength={3} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <Button
                type="submit"
                className="w-full"
                disabled={mutation.isPending}
              >
                {mutation.isPending ? "Sending..." : "Submit Invoice"}
              </Button>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}
