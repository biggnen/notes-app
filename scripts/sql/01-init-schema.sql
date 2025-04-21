-- create the database tables

-- documents table - stores main document information
create table documents (
    document_id uuid primary key default gen_random_uuid(),
    title varchar(255) not null,
    created_at timestamp with time zone default current_timestamp,
    updated_at timestamp with time zone default current_timestamp
);

-- document content table - stores the actual text content
create table document_content (
    document_id uuid primary key references documents(document_id) on delete cascade,
    content text
);

-- topics table - maps documents to topics/tags
create table topics (
    topic_id serial primary key,
    document_id uuid references documents(document_id) on delete cascade,
    topic_name varchar(80) not null,
    unique (document_id, topic_name)
);

-- create index for faster topic searches
create index idx_topics_topic_name on topics(topic_name);

-- document relationships - stores links between documents
create table document_relationships (
    relationship_id serial primary key,
    source_document_id uuid references documents(document_id) on delete cascade,
    target_document_id uuid references documents(document_id) on delete cascade,
    relationship_type varchar(50) default 'link',
    created_at timestamp with time zone default current_timestamp,
    unique (source_document_id, target_document_id, relationship_type)
);

-- create indexes for faster relationship queries
create index idx_doc_rel_source on document_relationships(source_document_id);
create index idx_doc_rel_target on document_relationships(target_document_id);

-- attachments table - stores metadata about attachments
create table attachments (
    attachment_id uuid primary key default gen_random_uuid(),
    document_id uuid references documents(document_id) on delete cascade,
    filename varchar(255) not null,
    file_type varchar(100) not null,
    file_size integer not null,
    created_at timestamp with time zone default current_timestamp
);

-- attachment content - stores the actual binary data
create table attachment_content (
    attachment_id uuid primary key references attachments(attachment_id) on delete cascade,
    content bytea not null  -- binary content of the file
);

-- create index for faster attachment lookups by document
create index idx_attachments_document_id on attachments(document_id);

-- function to update the updated_at timestamp
create or replace function update_modified_column()
returns trigger as $$
begin
    new.updated_at = current_timestamp;
    return new;
end;
$$ language 'plpgsql';

-- trigger to automatically update the modified timestamp on documents
create trigger update_document_modtime
before update on documents
for each row
execute function update_modified_column();

-- create a search function using postgresql's full-text search
create or replace function search_documents(search_query text)
returns table (
    document_id uuid,
    title varchar(255),
    content_preview text,
    rank float
) as $$
begin
    return query
    select
        d.document_id,
        d.title,
        substring(dc.plain_text_content, 1, 200) as content_preview,
        ts_rank(
            to_tsvector('english', d.title || ' ' || coalesce(dc.plain_text_content, '')),
            to_tsquery('english', search_query)
        ) as rank
    from
        documents d
    left join
        document_content dc on d.document_id = dc.document_id
    where
        to_tsvector('english', d.title || ' ' || coalesce(dc.plain_text_content, '')) @@ to_tsquery('english', search_query)
    order by
        rank desc;
end;
$$ language 'plpgsql';
