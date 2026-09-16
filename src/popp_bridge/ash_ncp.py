"""NCP-side ASH protocol for exposing raw EZSP to stock Bellows/ZHA."""

import asyncio

from bellows import ash
import bellows.types as t


class AshNcpProtocol(ash.AshProtocol):
    """ASH peer used on the adapter side of the bridge."""

    def __init__(self, *args, reset_handler=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.nak_state = False
        self._reset_handler = reset_handler
        self._reset_task = None
        self.reset_in_progress = False

    def frame_received(self, frame: ash.AshFrame) -> None:
        if self._ncp_reset_code is not None and not isinstance(frame, ash.RstFrame):
            self._write_frame(
                ash.ErrorFrame(version=2, reset_code=self._ncp_reset_code)
            )
            return

        if self.nak_state:
            asyncio.get_running_loop().call_later(
                2 * self._t_rx_ack,
                lambda: self._write_frame(
                    ash.NakFrame(res=0, ncp_ready=0, ack_num=self._rx_seq)
                ),
            )
            return
        super().frame_received(frame)

    def _enter_ncp_error_state(self, code: t.NcpResetCode | None) -> None:
        self._ncp_reset_code = code
        self._ncp_state = (
            ash.NcpState.CONNECTED if code is None else ash.NcpState.FAILED
        )
        if self._ncp_state is ash.NcpState.FAILED:
            self._write_frame(
                ash.ErrorFrame(version=2, reset_code=self._ncp_reset_code)
            )

    def _finish_host_reset(self) -> None:
        super().rst_frame_received(ash.RstFrame())
        self._tx_seq = 0
        self._rx_seq = 0
        self._change_ack_timeout(ash.T_RX_ACK_INIT)
        self._enter_ncp_error_state(None)
        self._write_frame(
            ash.RStackFrame(version=2, reset_code=t.NcpResetCode.RESET_SOFTWARE)
        )

    async def _run_host_reset(self) -> None:
        self.reset_in_progress = True
        try:
            await self._reset_handler()
        except Exception:
            if self._transport is not None:
                self._transport.close()
            return
        finally:
            self.reset_in_progress = False
        self._finish_host_reset()

    def rst_frame_received(self, frame: ash.RstFrame) -> None:
        if self._reset_handler is None:
            self._finish_host_reset()
            return
        if self._reset_task is not None and not self._reset_task.done():
            return
        self._reset_task = asyncio.create_task(self._run_host_reset())

    async def _send_data_frame(self, frame: ash.AshFrame) -> None:
        try:
            return await super()._send_data_frame(frame)
        except TimeoutError:
            self._enter_ncp_error_state(
                t.NcpResetCode.ERROR_EXCEEDED_MAXIMUM_ACK_TIMEOUT_COUNT
            )
            raise

    def send_reset(self) -> None:
        raise NotImplementedError("NCP-side bridge does not initiate ASH resets")
