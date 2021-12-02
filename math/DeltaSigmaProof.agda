module DeltaSigmaProof where
  open import Agda.Builtin.FromNat
  open import Algebra
  open import Algebra.Structures
  import Algebra.Operations.Semiring
  import Data.Nat as Nat
  open Nat using (ℕ)
  import Data.Nat.Literals
  open import Data.Integer
  import Data.Integer.Literals
  open import Data.Integer.Properties
  open import Relation.Nullary.Decidable

  instance
    ℕ-fromNat = Data.Nat.Literals.number
    ℤ-fromNat = Data.Integer.Literals.number

  open Algebra.Operations.Semiring (record
    { Carrier = _
    ; _≈_ = _
    ; _+_ = _
    ; _*_ = _
    ; 0# = _
    ; 1# = _
    ; isSemiring = IsCommutativeSemiring.isSemiring +-*-isCommutativeSemiring
    })

  record HalfOpenRange : Set where
    constructor half-open
    field
      min : ℤ
      max : ℤ
      min≤max : min ≤ max

  record _∈_ (n : ℤ) (R : HalfOpenRange) : Set where
    constructor is-in
    open HalfOpenRange R
    field
      n≥min : n ≥ min
      n<max : n < max

  Signed : (N : ℕ) {N≥1 : True (1 Nat.≤? N)} → HalfOpenRange
  Signed Nat.zero {()}
  Signed (Nat.suc N-1) = half-open min max min≤max
    where
      min = - (2 ^ N-1)
      max = 2 ^ N-1 - 1
      2^N-1>0 : 2 ^ N-1 > 0
      2^N-1>0 = {!!}
      min≤max : min ≤ max
      min≤max = {!!}

  record Sample (N : ℕ) : Set where
    constructor sample
    field
      value : ℤ
      -- n-bit : value ∈ half-open
