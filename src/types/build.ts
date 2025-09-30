export interface Server {
  rackID: string;
  hostname: string;
  dbid: string;
  serial_number: string;
  percent_built: number;
  assigned_status: string;
}

export interface BuildStatus {
  cbg: Server[];
  dub: Server[];
  dal: Server[];
}

export type Region = 'CBG' | 'DUB' | 'DAL';

export interface RackSlot {
  position: string;
  servers: Server[];
}