import mock

def stub_raise_later():
    '''
    Returns a mock objects that will raise an exception
    on the third call.

    It's used to abort infinite loops. Just mock a method that is
    called inside the loop and ensure `Exception('break')` is raised

    '''
    def continue_loop():
        pass
    def break_loop():
        raise Exception('break')
    side_effects = [continue_loop, continue_loop, break_loop]

    m = mock.Mock()
    m.side_effect = lambda *args: side_effects.pop(0)()
    return m
