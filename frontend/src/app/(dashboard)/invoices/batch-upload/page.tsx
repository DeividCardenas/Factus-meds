"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import Papa from "papaparse";
import { useMutation } from "@tanstack/react-query";
import { UploadCloud } from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { useToast } from "@/components/ui/use-toast";

interface CsvRow {
  customer_id: string;
  total: string;
  currency?: string;
}

const DEFAULT_CURRENCY = "COP";

interface InvoicePayload {
  source: string;
  invoices: {
    external_id: string;
    customer_id: string;
    issued_at: string;
    total: number;
    currency: string;
  }[];
}

async function submitBatch(payload: InvoicePayload): Promise<{ count: number }> {
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
    throw new Error(
      (errorData as { message?: string }).message ??
        `Request failed with status ${response.status}`
    );
  }

  return { count: payload.invoices.length };
}

export default function BatchUploadPage() {
  const { toast } = useToast();
  const [recordCount, setRecordCount] = useState<number | null>(null);

  const mutation = useMutation({
    mutationFn: submitBatch,
    onSuccess: (data) => {
      toast({
        title: "Upload successful!",
        description: `Success! ${data.count} invoices sent to the processing queue.`,
      });
      setRecordCount(null);
    },
    onError: (error: Error) => {
      toast({
        variant: "destructive",
        title: "Upload failed",
        description: error.message,
      });
      setRecordCount(null);
    },
  });

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file) return;

      Papa.parse<CsvRow>(file, {
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
          const validRows = results.data.filter(
            (row) =>
              row.customer_id &&
              row.customer_id.trim() !== "" &&
              row.total &&
              !isNaN(Number(row.total)) &&
              Number(row.total) > 0
          );

          if (validRows.length === 0) {
            toast({
              variant: "destructive",
              title: "Invalid CSV",
              description:
                "No valid rows found. Ensure the CSV has customer_id and total columns.",
            });
            return;
          }

          const payload: InvoicePayload = {
            source: "csv_bulk_upload",
            invoices: validRows.map((row) => ({
              external_id: `BULK-${crypto.randomUUID()}`,
              customer_id: row.customer_id.trim(),
              issued_at: new Date().toISOString(),
              total: Number(row.total),
              currency: row.currency?.trim() || DEFAULT_CURRENCY,
            })),
          };

          setRecordCount(payload.invoices.length);
          mutation.mutate(payload);
        },
        error: (error: Error) => {
          toast({
            variant: "destructive",
            title: "CSV parse error",
            description: error.message,
          });
        },
      });
    },
    [mutation, toast]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "text/csv": [".csv"] },
    multiple: false,
    disabled: mutation.isPending,
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">Bulk Upload</h1>
      <Card>
        <CardHeader>
          <CardTitle>Upload CSV File</CardTitle>
          <CardDescription>
            Upload a CSV file with headers: <code>customer_id</code>,{" "}
            <code>total</code>, <code>currency</code> (optional, defaults to COP)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            {...getRootProps()}
            className={[
              "flex flex-col items-center justify-center gap-4 rounded-xl border-2 border-dashed p-12 text-center transition-colors",
              mutation.isPending
                ? "cursor-not-allowed opacity-60 border-muted-foreground/30 bg-muted/20"
                : isDragActive
                ? "border-primary bg-primary/5 cursor-copy"
                : "border-muted-foreground/30 bg-muted/10 hover:border-primary/60 hover:bg-muted/20 cursor-pointer",
            ].join(" ")}
          >
            <input {...getInputProps()} />
            <UploadCloud
              className={[
                "h-12 w-12 transition-colors",
                isDragActive ? "text-primary" : "text-muted-foreground",
              ].join(" ")}
            />
            {mutation.isPending ? (
              <div className="space-y-1">
                <p className="text-sm font-medium text-foreground">
                  Processing {recordCount?.toLocaleString() ?? "your"} records…
                  Please wait
                </p>
                <p className="text-xs text-muted-foreground">
                  Sending data to the processing queue
                </p>
              </div>
            ) : isDragActive ? (
              <p className="text-sm font-medium text-primary">
                Drop your CSV file here
              </p>
            ) : (
              <div className="space-y-1">
                <p className="text-sm font-medium text-foreground">
                  Drag &amp; drop your CSV file here, or click to select
                </p>
                <p className="text-xs text-muted-foreground">
                  Only .csv files are accepted
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
