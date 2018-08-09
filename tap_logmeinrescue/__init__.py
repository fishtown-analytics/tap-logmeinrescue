import json
import singer
import sys
import tap_framework
import tap_logmeinrescue.client
import tap_logmeinrescue.streams

LOGGER = singer.get_logger()


class LogMeInRescueRunner(tap_framework.Runner):

    def do_discover(self):
        LOGGER.info("Starting discovery.")

        catalog = []
        technicians_stream = None
        technicians_substreams = []

        for available_stream in self.available_streams:
            if available_stream.TABLE == 'technicians':
                technicians_stream = available_stream(
                    self.config, self.state, None, self.client)

            else:
                technicians_substreams += [available_stream(
                    self.config, self.state, None, self.client)]

        technicians_stream.catalog = singer.catalog.CatalogEntry(
            schema=singer.schema.Schema.from_dict(
                technicians_stream.get_schema()))

        catalog += technicians_stream.generate_catalog()

        technician_ids = technicians_stream.sync_data(return_ids=True)

        for technicians_substream in technicians_substreams:
            first_response = technicians_substream.sync_data(
                parent_ids=technician_ids,
                return_first_response=True
            )

            header = technicians_substream.get_header(first_response)
            custom_field_schema = technicians_substream \
                .header_to_string_schema(header)

            catalog += technicians_substream.generate_catalog(
                custom_field_schema)

        json.dump({'streams': catalog}, sys.stdout, indent=4)

    def get_streams_to_replicate(self):
        streams = []
        technicians_stream = None
        technicians_substreams = []

        for stream_catalog in self.catalog.streams:
            if not stream_catalog.schema.selected:
                LOGGER.info("'{}' is not marked selected, skipping."
                            .format(stream_catalog.stream))
                continue

            for available_stream in self.available_streams:
                if available_stream.matches_catalog(stream_catalog):
                    if not available_stream.requirements_met(self.catalog):
                        raise RuntimeError(
                            "{} requires that that the following are "
                            "selected: {}"
                            .format(stream_catalog.stream,
                                    ','.join(available_stream.REQUIRES)))

                    if available_stream.TABLE == 'technicians':
                        technicians_stream = available_stream(
                            self.config, self.state, stream_catalog,
                            self.client)

                    else:
                        technicians_substreams = [available_stream(
                            self.config, self.state, stream_catalog,
                            self.client)]

        if technicians_stream is not None:
            technicians_stream.substreams = technicians_substreams
            streams.append(technicians_stream)

        return streams


@singer.utils.handle_top_exception(LOGGER)
def main():
    args = singer.utils.parse_args(
        required_config_keys=['username', 'password', 'start_date'])

    client = tap_logmeinrescue.client.LogMeInRescueClient(args.config)

    runner = LogMeInRescueRunner(
        args, client, tap_logmeinrescue.streams.AVAILABLE_STREAMS)

    if args.discover:
        runner.do_discover()
    else:
        runner.do_sync()


if __name__ == '__main__':
    main()