export interface Server {
  rackID: string;
  hostname: string;
  dbid: string;
  serial_number: string;
  percent_built: number;
  assigned_status: string;
  machine_type: string;
  status: string;
}

// BuildStatus is now dynamically keyed by region codes from config
export interface BuildStatus {
  [region: string]: Server[];
}

// Region type is now a string since regions are loaded dynamically from config
export type Region = string;

export interface RackSlot {
  position: string;
  servers: Server[];
}