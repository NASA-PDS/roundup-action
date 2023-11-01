# encoding: utf-8

'''🤠 PDS Roundup: Assemblies. An assembly is responsible for conducting the roundup.'''

from .step import StepName
import logging

_logger = logging.getLogger(__name__)


class Assembly(object):
    '''Generic assembly whose job is to do a roundup; subclasses provide refined assembly
    behavior.
    '''
    def __init__(self, context, stepNames=[]):
        '''Assemblies have a ``context`` that tells the morphology (location and environment) of
        the roundup and the names of the steps (``stepNames``) they'll need to do
        .'''
        self.context, self.stepNames = context, stepNames

    def __repr__(self):
        return f'<{self.__class__.__name__}(context={self.context},#stepNames={len(self.stepNames)})>'

    def roundup(self):
        '''Round 'em up, pardner! 🤠'''
        _logger.debug(
            '🤠 Preparing %s roundup for %r with the following steps: %r',
            self.__class__.__name__, self.context, self.stepNames
        )
        steps = []
        for stepName in self.stepNames:
            _logger.debug("Creating step %s", stepName)
            step = self.context.createStep(stepName, self)
            if step:
                _logger.debug("Adding step %s", step.__class__.__name__)
                steps.append(step)
            else:
                _logger.info('For context %r no step was available for %s; ignoring this step', self.context, stepName)
        _logger.debug('Executing roundup')
        for step in steps:
            _logger.info("🏎▁▂▃▄▅▆▆▇▇██💨 EXECUTING step %s", step.__class__.__name__)
            step.execute()

    def isStable(self):
        '''By default, assemblies will always be for "unstable" or in-development releases, so this
        always returns False. Subclasses might override this.
        '''
        return False

    # 🤔 Other characteristics of the assembly can go here. For example, we might replace
    # ``isStable`` (which isn't very "OO") with methods that return attributes of the assembly
    # like "what PyPI do I use" and "how do we mark a snapshot", etc.


class NoOpAssembly(Assembly):
    '''A special assembly that does nothing but using a single step, namely ``StepName.null``.'''
    def __init__(self, context):
        super(NoOpAssembly, self).__init__(context, [StepName.null])


class PDSAssembly(Assembly):
    '''The PDS-flavored assembly which has 9 different steps'''
    pdsSteps = [
        StepName.preparation,
        StepName.unitTest,
        StepName.integrationTest,
        StepName.docs,
        StepName.versionBump,
        StepName.build,
        StepName.artifactPublication,
        # NASA-PDS/roundup-action#29: generate the requirements before tagging the release
        StepName.requirements,
        # NASA-PDS/roundup-action#29: generate the changelog before tagging the release
        StepName.changeLog,
        StepName.githubRelease,
        StepName.docPublication,
        # NASA-PDS/roundup-action#124: split version bumping from version committing
        StepName.versionCommit,
        StepName.cleanup,
    ]

    def __init__(self, context):
        super(PDSAssembly, self).__init__(context, self.pdsSteps)


class StablePDSAssembly(PDSAssembly):
    '''The stable (production) PDS assembly'''
    def isStable(self):
        return True


class UnstablePDSAssembly(PDSAssembly):
    '''The unstable (in-development) PDS assembly'''
    pass


class IntegrativePDSAssembly(UnstablePDSAssembly):
    '''An assembly for integrations; this is unstable but omits the requirements and
    changelog generation steps.

    See https://github.com/NASA-PDS/roundup-action/issues/46 for more information.
    '''
    pdsSteps = [
        StepName.preparation,
        StepName.unitTest,
        StepName.integrationTest,
        StepName.docs,
        StepName.build,
        StepName.artifactPublication,
        StepName.githubRelease,
        StepName.docPublication,
        StepName.cleanup,
    ]


class EnvironmentalAssembly(Assembly):
    '''An assembly whose actions are controlled through the environment.

    To take advantage of this assembly, set these two environment variables before starting:

    • ROUNDUP_STABLE set to ``True`` (or ``true`` or ``1``) for a stable assembly, otherwise unstable
    • ROUNDUP_STEPS set to a comma-separated sequence of step names to use, like ``preparation,build,cleanup``
      See the ``pds.roundup.step.StepName`` enumeration for the possible step names.

    Then pass the ``--assembly env`` command-line argument to the ``roundup`` executable.
    '''
    def __init__(self, context, stepNames=[]):
        self._isStable = context.environ.get('ROUNDUP_STABLE', 'False').lower().strip() in ('true', '1')
        super().__init__(context, [StepName(i) for i in context.environ.get('ROUNDUP_STEPS', '').strip().split(',')])

    def isStable(self):
        return self._isStable
