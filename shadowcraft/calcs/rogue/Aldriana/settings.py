from shadowcraft.core import exceptions

class Settings(object):
    # Settings object for AldrianasRogueDamageCalculator.

    def __init__(self, cycle, time_in_execute_range=.35, tricks_on_cooldown=True, response_time=.5, latency=.03, dmg_poison='dp', utl_poison=None,
                 duration=300, use_opener='always', opener_name='default', is_pvp=False, stormlash=False, shiv_interval=0, adv_params=None,
                 merge_damage=True, num_boss_adds=0, feint_interval=0):
        self.cycle = cycle
        self.time_in_execute_range = time_in_execute_range
        self.tricks_on_cooldown = tricks_on_cooldown
        self.response_time = response_time
        self.latency = latency
        self.dmg_poison = dmg_poison
        self.utl_poison = utl_poison
        self.duration = duration
        self.use_opener = use_opener # Allowed values are 'always' (vanish/shadowmeld on cooldown), 'opener' (once per fight) and 'never'
        self.opener_name = opener_name
        self.is_pvp = is_pvp
        self.use_stormlash = stormlash
        self.feint_interval = feint_interval
        self.merge_damage = merge_damage
        self.num_boss_adds = max(num_boss_adds, 0)
        self.shiv_interval = float(shiv_interval)
        self.adv_params = self.interpret_adv_params(adv_params)
        if self.shiv_interval < 10 and not self.shiv_interval == 0:
            self.shiv_interval = 10
        allowed_openers_per_spec = {
            'assassination': ('mutilate', 'dispatch', 'envenom'),
            'combat': ('sinister_strike', 'revealing_strike', 'eviscerate'),
            'subtlety': ('eviscerate')
        }
        allowed_openers = allowed_openers_per_spec[self.get_spec()] + ('ambush', 'garrote', 'default', 'cpg')
        if opener_name not in allowed_openers:
            raise exceptions.InvalidInputException(_('Opener {opener} is not allowed in {cycle} cycles.').format(opener=opener_name, cycle=self.get_spec()))
        if opener_name == 'default':
            default_openers = {
                'assassination': 'mutilate',
                'combat': 'ambush',
                'subtlety': 'ambush'}
            self.opener_name = default_openers[self.get_spec()]
        if dmg_poison not in (None, 'dp', 'wp'):
            raise exceptions.InvalidInputException(_('You can only choose Deadly(dp) or Wound(wp) as a damage poison'))
        if utl_poison not in (None, 'cp', 'mnp', 'lp', 'pp'):
            raise exceptions.InvalidInputException(_('You can only choose Crippling(cp), Mind-Numbing(mnp), Leeching(lp) or Paralytic(pp) as a non-lethal poison'))

    def get_spec(self):
        return self.cycle._cycle_type
    
    def interpret_adv_params(self, s=""):
        data = {}
        max_effects = 8
        current_effects = 0
        if s != "" and s:
            for e in s.split(';'):
                if e != "":
                    tmp = e.split(':')
                    try:
                        data[tmp[0].strip().lower()] = tmp[1].strip().lower() #strip() and lower() needed so that everyone is on the same page                        print data[tmp[0].strip().lower()] + ' : ' + tmp[0].strip().lower()
                        current_effects += 1
                        if current_effects == max_effects:
                            return data
                    except:
                        raise exceptions.InvalidInputException(_('Advanced Parameter ' + e + ' found corrupt. Properly structure params and try again.'))
        return data
    
    def is_assassination_rogue(self):
        return self.get_spec() == 'assassination'

    def is_combat_rogue(self):
        return self.get_spec() == 'combat'

    def is_subtlety_rogue(self):
        return self.get_spec() == 'subtlety'

class Cycle(object):
    # Base class for cycle objects.  Can't think of anything that particularly
    # needs to go here yet, but it seems worth keeping options open in that
    # respect.

    # When subclassing, define _cycle_type to be one of 'assassination',
    # 'combat', or 'subtlety' - this is how the damage calculator makes sure
    # you have an appropriate cycle object to go with your talent trees, etc.
    _cycle_type = ''


class AssassinationCycle(Cycle):
    _cycle_type = 'assassination'

    allowed_values = (1, 2, 3, 4, 5)

    def __init__(self, min_envenom_size_non_execute=4, min_envenom_size_execute=5, prioritize_rupture_uptime_non_execute=True, prioritize_rupture_uptime_execute=True, stack_cds=False):
        assert min_envenom_size_non_execute in self.allowed_values
        self.min_envenom_size_non_execute = min_envenom_size_non_execute

        assert min_envenom_size_execute in self.allowed_values
        self.min_envenom_size_execute = min_envenom_size_execute
        
        self.stack_cds = stack_cds

        # There are two fundamental ways you can manage rupture; one is to
        # reapply with whatever CP you have as soon as you can after the old
        # rupture drops; we will call this priorotizing uptime over size.
        # The second is to use ruptures that are the same size as your
        # envenoms, which we will call prioritizing size over uptime. True
        # means the first of these options; False means the second.
        # There are theoretically other things you can do (say, 4+ envenom and
        # 5+ ruptures) but such things are significantly harder to model so I'm
        # not going to worry about them until we have reason to believe they're
        # actually better.
        self.prioritize_rupture_uptime_non_execute = prioritize_rupture_uptime_non_execute
        self.prioritize_rupture_uptime_execute = prioritize_rupture_uptime_execute


class CombatCycle(Cycle):
    _cycle_type = 'combat'

    def __init__(self, use_rupture=True, ksp_immediately=True, revealing_strike_pooling=True, blade_flurry=False, stack_cds=True, bf_targets=1, weapon_swap=False):
        self.blade_flurry = bool(blade_flurry)
        self.use_rupture = bool(use_rupture)
        self.ksp_immediately = bool(ksp_immediately) # Determines whether to KSp the instant it comes off cool or wait until Bandit's Guile stacks up.
        self.revealing_strike_pooling = bool(revealing_strike_pooling)
        self.stack_cds = bool(stack_cds) # This refers specifically to stacking SB and AR
        self.weapon_swap = weapon_swap # Tells the combat calculations to use the second oh weapon for KS, and weapon swap before and after the cast.

class SubtletyCycle(Cycle):
    _cycle_type = 'subtlety'

    def __init__(self, raid_crits_per_second, use_hemorrhage='24', sub_sb_timing='shd'):
        self.raid_crits_per_second = raid_crits_per_second #used to calculate HAT procs per second.
        self.use_hemorrhage = use_hemorrhage # Allowed values are 'always' (main CP generator),
                                                                 #'never' (default to backstab),
                                                                 # or a number denoting the interval in seconds between applications
        self.sub_sb_timing = sub_sb_timing #Sets when ShD is cast: 'shd', 'fw', 'other'