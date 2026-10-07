import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "Asistente digital | ARCAT",
  description: "Consulta guiada de trámites y servicios de ARCAT.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
