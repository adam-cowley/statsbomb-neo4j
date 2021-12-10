interface StatsbombEventType {
  id: number;
  name: string;
}

interface Team {
  id: number;
  name: string;
}

export interface StatsbombEvent {
  id: string;
  type: StatsbombEventType;
  location: number[];
  possession: number;
  possession_team: Team;
  [key: string]: any;
}
