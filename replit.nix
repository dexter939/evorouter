{pkgs}: {
  deps = [
    pkgs.which
    pkgs.miniupnpc
    pkgs.sqlite
    pkgs.postgresql
    pkgs.openssl
  ];
}
