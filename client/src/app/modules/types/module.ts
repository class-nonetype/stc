type SidenavOption = {
  name: string;
  route?: string;
  icon: string;
  onClick?: (event?: MouseEvent) => void | Promise<void>;
};
