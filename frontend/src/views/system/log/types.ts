export interface searchDataType {
    request_path?: string;
    creator?: number;
    creator_name?: string;
    date_range?: [string, string];
}

export interface tableDataType {
    id?: number;
    index?: number;
    request_path?: string;
    request_method?: string;
    request_ip?: string;
    request_browser?: string;
    request_os?: string;
    response_code?: number;
    request_payload?: string;
    response_json?: string;
    description?: string;
    creator?: creatorType;
    created_at?: string;
    updated_at?: string;
}

export interface searchCreatorDataType {
    name?: string;
    available?: string;
}

export interface creatorType {
    id?: number;
    name?: string;
    username?: string;
}