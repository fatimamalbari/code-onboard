export class Config {
    readonly dbHost: string;
    readonly dbPort: number;

    constructor() {
        this.dbHost = process.env.DB_HOST || 'localhost';
        this.dbPort = parseInt(process.env.DB_PORT || '5432');
    }

    getConnectionString(): string {
        return `postgresql://${this.dbHost}:${this.dbPort}/app`;
    }
}
