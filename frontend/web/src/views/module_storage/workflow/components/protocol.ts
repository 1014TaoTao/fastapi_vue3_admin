/**
 * 存储协议展示工具：颜色 / 标签
 * 供画布节点、节点配置面板、节点面板统一使用，避免三处重复定义。
 */
export const PROTOCOL_COLOR: Record<string, string> = {
  local: "#67c23a",
  ftp: "#409eff",
  ftps: "#409eff",
  sftp: "#409eff",
  s3: "#e6a23c",
  oss: "#e6a23c",
  obs: "#e6a23c",
  cos: "#e6a23c",
};

export const PROTOCOL_LABEL: Record<string, string> = {
  local: "本地",
  ftp: "FTP",
  ftps: "FTPS",
  sftp: "SFTP",
  s3: "S3",
  oss: "OSS",
  obs: "OBS",
  cos: "COS",
};

/** 协议主题色（未知协议回退灰色） */
export function protocolColor(protocol?: string): string {
  return PROTOCOL_COLOR[(protocol || "").toLowerCase()] || "#909399";
}

/** 协议中文标签（未知协议原样返回大写） */
export function protocolLabel(protocol?: string): string {
  const p = (protocol || "").toLowerCase();
  return PROTOCOL_LABEL[p] || p || "存储";
}

/** 协议标签 + 主机地址 */
export function protocolText(protocol?: string, host?: string): string {
  const label = protocolLabel(protocol);
  return host ? `${label} · ${host}` : label;
}
