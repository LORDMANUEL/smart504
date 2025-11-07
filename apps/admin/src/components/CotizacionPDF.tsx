'use client';

import React from 'react';
import { Page, Text, View, Document, StyleSheet } from '@react-pdf/renderer';
import { Cotizacion } from '@ecommerce/sdk';

// Create styles
const styles = StyleSheet.create({
  page: {
    padding: 30,
    fontFamily: 'Helvetica',
    fontSize: 11,
  },
  header: {
    marginBottom: 20,
    textAlign: 'center',
    fontSize: 24,
    fontWeight: 'bold',
  },
  section: {
    marginBottom: 10,
  },
  title: {
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 8,
    borderBottom: 1,
    borderBottomColor: '#cccccc',
    paddingBottom: 4,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  table: {
    width: '100%',
    marginTop: 10,
  },
  tableHeader: {
    flexDirection: 'row',
    backgroundColor: '#f2f2f2',
    fontWeight: 'bold',
  },
  tableRow: {
    flexDirection: 'row',
    borderBottom: 1,
    borderBottomColor: '#cccccc',
  },
  col: {
    padding: 5,
    borderRight: 1,
    borderRightColor: '#cccccc',
  }
});

interface CotizacionPDFProps {
  cotizacion: Cotizacion;
}

export const CotizacionPDF: React.FC<CotizacionPDFProps> = ({ cotizacion }) => {
  const vehiculo = cotizacion.vehiculo as any;
  const partes = cotizacion.lineasPartes as any[];
  const manoDeObra = cotizacion.lineasManoObra as any[];

  return (
    <Document>
      <Page size="A4" style={styles.page}>
        <Text style={styles.header}>Cotización de Repuestos y Servicios</Text>

        <View style={styles.section}>
          <Text style={styles.title}>Información General</Text>
          <View style={styles.row}><Text>ID Cotización:</Text><Text>{cotizacion.id}</Text></View>
          <View style={styles.row}><Text>Fecha:</Text><Text>{new Date(cotizacion.createdAt).toLocaleDateString()}</Text></View>
        </View>

        <View style={styles.section}>
          <Text style={styles.title}>Vehículo</Text>
          <View style={styles.row}><Text>Marca/Modelo:</Text><Text>{vehiculo.marca} {vehiculo.modelo}</Text></View>
          <View style={styles.row}><Text>Año:</Text><Text>{vehiculo.anio}</Text></View>
        </View>

        <View style={styles.section}>
          <Text style={styles.title}>Partes y Repuestos</Text>
          <View style={styles.table}>
            <View style={styles.tableHeader}>
              <Text style={{...styles.col, width: '40%'}}>Descripción</Text>
              <Text style={{...styles.col, width: '20%'}}>Cantidad</Text>
              <Text style={{...styles.col, width: '20%'}}>Precio Unit.</Text>
              <Text style={{...styles.col, width: '20%'}}>Subtotal</Text>
            </View>
            {partes.map((item, i) => (
              <View key={i} style={styles.tableRow}>
                <Text style={{...styles.col, width: '40%'}}>{item.nombre}</Text>
                <Text style={{...styles.col, width: '20%'}}>{item.cantidad}</Text>
                <Text style={{...styles.col, width: '20%'}}>L {item.precio.toFixed(2)}</Text>
                <Text style={{...styles.col, width: '20%'}}>L {(item.cantidad * item.precio).toFixed(2)}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Total General */}
        <View style={{...styles.section, marginTop: 20}}>
            <View style={{...styles.row, fontSize: 16, fontWeight: 'bold'}}>
                <Text>Total:</Text>
                <Text>L {cotizacion.total.toFixed(2)}</Text>
            </View>
        </View>
      </Page>
    </Document>
  );
};
