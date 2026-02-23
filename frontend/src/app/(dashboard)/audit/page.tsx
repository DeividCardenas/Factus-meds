"use client";

import { gql } from "@apollo/client";
import { useQuery } from "@apollo/client/react";
import { AlertCircle, QrCode } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Invoice, InvoiceStatus } from "@/types/invoice";

const GET_INVOICES = gql`
  query GetInvoices {
    invoices {
      external_id
      customer_id
      issued_at
      total
      tax_amount
      status
      factus_invoice_id
      qr_url
      error_message
    }
  }
`;

function getStatusVariant(
  status: InvoiceStatus
): "success" | "warning" | "destructive" | "secondary" {
  if (status === "SUCCESS" || status === "SENT") return "success";
  if (status === "PENDING") return "warning";
  if (status === "FAILED" || status === "ERROR") return "destructive";
  return "secondary";
}

export default function AuditPage() {
  const { loading, error, data } = useQuery<{ invoices: Invoice[] }>(
    GET_INVOICES
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 rounded-md border border-destructive bg-destructive/10 p-4 text-destructive">
        <AlertCircle className="h-5 w-5 shrink-0" />
        <span>Error al cargar las facturas: {error.message}</span>
      </div>
    );
  }

  const invoices: Invoice[] = data?.invoices ?? [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">Auditoría</h1>
      <Card>
        <CardHeader>
          <CardTitle>Registro de auditoría de facturas</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID Externo</TableHead>
                <TableHead>Cliente</TableHead>
                <TableHead>Fecha</TableHead>
                <TableHead>Total</TableHead>
                <TableHead>Impuesto</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>ID Factus</TableHead>
                <TableHead>Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {invoices.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={8}
                    className="text-center text-muted-foreground"
                  >
                    No hay facturas disponibles.
                  </TableCell>
                </TableRow>
              ) : (
                invoices.map((invoice) => (
                  <TableRow key={invoice.external_id}>
                    <TableCell className="font-mono text-xs">
                      {invoice.external_id}
                    </TableCell>
                    <TableCell>{invoice.customer_id}</TableCell>
                    <TableCell>
                      {new Date(invoice.issued_at).toLocaleDateString("es-CO")}
                    </TableCell>
                    <TableCell>
                      {invoice.total.toLocaleString("es-CO", {
                        style: "currency",
                        currency: "COP",
                        minimumFractionDigits: 0,
                      })}
                    </TableCell>
                    <TableCell>
                      {invoice.tax_amount.toLocaleString("es-CO", {
                        style: "currency",
                        currency: "COP",
                        minimumFractionDigits: 0,
                      })}
                    </TableCell>
                    <TableCell>
                      <Badge variant={getStatusVariant(invoice.status)}>
                        {invoice.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {invoice.factus_invoice_id}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {invoice.qr_url && (
                          <a
                            href={invoice.qr_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            title="Ver código QR"
                            className="text-primary hover:text-primary/80 transition-colors"
                          >
                            <QrCode className="h-5 w-5" />
                          </a>
                        )}
                        {invoice.error_message && (
                          <span title={invoice.error_message}>
                            <AlertCircle className="h-5 w-5 text-destructive" />
                          </span>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

