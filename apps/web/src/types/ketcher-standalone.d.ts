declare module "ketcher-standalone" {
  export class StandaloneStructServiceProvider {
    constructor(...args: any[]);
    mode: string;
    createStructService(...args: any[]): any;
  }
}
