SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

-- users are split into two tables for future option of adding more authentication providers
-- such as OAuth or SAML providers
CREATE TABLE public.users
(
    uuid uuid NOT NULL,
    username character varying(128) COLLATE pg_catalog."default" NOT NULL,
    providers_data jsonb,
    providers character varying(128)[] COLLATE pg_catalog."default" NOT NULL,
    suspended boolean NOT NULL DEFAULT FALSE,
    role character varying(16) COLLATE pg_catalog."default" NOT NULL DEFAULT USER,
    created timestamp with time zone NOT NULL DEFAULT now(),
    CONSTRAINT users_pkey PRIMARY KEY (uuid),
    CONSTRAINT uq_user_username UNIQUE (username)

)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;


CREATE TABLE public.local_users
(
    user_uuid uuid NOT NULL,
    pwd_hash character(60) COLLATE pg_catalog."default" NOT NULL,
    force_pwd_change boolean NOT NULL DEFAULT FALSE,
    CONSTRAINT local_users_pkey PRIMARY KEY (user_uuid),
    CONSTRAINT local_user_uuid FOREIGN KEY (user_uuid)
        REFERENCES public.users (uuid) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;



ALTER TABLE public.gcodes
    ADD COLUMN IF NOT EXISTS user_uuid uuid;

ALTER TABLE public.gcodes DROP CONSTRAINT IF EXISTS gcode_user_uuid_fk;
ALTER TABLE public.gcodes
    ADD CONSTRAINT gcode_user_uuid_fk FOREIGN KEY (user_uuid)
    REFERENCES public.users (uuid) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;

CREATE INDEX IF NOT EXISTS fki_gcode_user_uuid_fk
    ON public.gcodes(user_uuid);

ALTER TABLE public.printjobs
    ADD COLUMN IF NOT EXISTS user_uuid uuid;

ALTER TABLE public.printjobs DROP CONSTRAINT IF EXISTS printjob_user_uuid_fk;
ALTER TABLE public.printjobs
    ADD CONSTRAINT printjob_user_uuid_fk FOREIGN KEY (user_uuid)
    REFERENCES public.users (uuid) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION
    NOT VALID;

CREATE INDEX IF NOT EXISTS fki_printjob_user_uuid_fk
    ON public.printjobs(user_uuid);

CREATE TABLE public.api_tokens
(
    user_uuid uuid NOT NULL,
    jti uuid NOT NULL,
    name character varying(128) COLLATE pg_catalog."default" NOT NULL,
    created timestamp with time zone NOT NULL DEFAULT now(),
    revoked boolean NOT NULL DEFAULT FALSE,
    CONSTRAINT api_tokens_pkey PRIMARY KEY (jti),
    CONSTRAINT api_tokens_uuid FOREIGN KEY (user_uuid)
        REFERENCES public.users (uuid) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

insert into public.users (uuid, username, role, providers, providers_data)
  values ('1b59f2e0-336f-4a1c-8caf-1f074fc43744', 'karmen', 'admin', '{"local"}', '{}')
  on conflict do nothing;

-- password is karmen3D
insert into public.local_users (user_uuid, pwd_hash, force_pwd_change)
  values ('1b59f2e0-336f-4a1c-8caf-1f074fc43744', '$2y$12$6w9ml13UTA2Re2GcqDHFJuVHB3WLlPPyg430vrve/hrjR5yWO0LYm', true)
  on conflict do nothing;
